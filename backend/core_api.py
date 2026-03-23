from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from canonical_schema import (
    canonical_to_payload,
    canonical_to_record,
    infer_source_format,
    record_to_canonical,
)
from collab.store import create_workspace
from compat.dna_format import export_dna_container, import_dna_container
from genomeforge_toolkit import (
    Feature,
    SequenceRecord,
    build_svg_map,
    design_primer_pair,
    find_all_occurrences,
    optimize_coding_sequence,
    parse_fasta,
    parse_genbank,
    sanitize_sequence,
    simulate_digest,
    simulate_pcr,
    to_embl,
    to_fasta,
    to_genbank,
)


RecordGetter = Callable[[], SequenceRecord]


def parse_embl(text: str) -> SequenceRecord:
    name = "Untitled"
    topology = "linear"
    in_features = False
    in_seq = False
    seq_chunks: List[str] = []
    feats: List[Feature] = []
    cur_feat: Feature | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("ID"):
            parts = line.split()
            if len(parts) >= 2:
                name = parts[1].strip(";")
            low = line.lower()
            if "circular" in low:
                topology = "circular"
            elif "linear" in low:
                topology = "linear"
        if line.startswith("FH"):
            in_features = True
            continue
        if line.startswith("SQ"):
            in_seq = True
            in_features = False
            continue
        if line.startswith("//"):
            break
        if in_features and line.startswith("FT"):
            body = line[2:].rstrip()
            if len(body.strip()) == 0:
                continue
            if body[:6].strip():
                key = body[:15].strip() or "misc_feature"
                loc = body[15:].strip()
                cur_feat = Feature(key=key, location=loc, qualifiers={})
                feats.append(cur_feat)
            else:
                q = body[15:].strip()
                if cur_feat and q.startswith("/") and "=" in q:
                    k, v = q[1:].split("=", 1)
                    cur_feat.qualifiers[k.strip()] = v.strip().strip('"')
            continue
        if in_seq:
            seq_chunks.append("".join(ch for ch in line if ch.isalpha()))
    seq = sanitize_sequence("".join(seq_chunks))
    rec = SequenceRecord(name=name, sequence=seq, topology=topology)
    rec.features = feats
    return rec


def parse_record(payload: Dict[str, Any]) -> SequenceRecord:
    if isinstance(payload.get("canonical_record"), dict):
        return canonical_to_record(payload["canonical_record"])
    content = (payload.get("content") or "").strip()
    name = (payload.get("name") or "Untitled").strip() or "Untitled"
    topology = (payload.get("topology") or "circular").strip().lower()
    if topology not in {"linear", "circular"}:
        topology = "linear"

    if not content:
        raise ValueError("Sequence input is empty")

    if content.startswith(">"):
        record = parse_fasta(content)
    elif content.lstrip().startswith("LOCUS"):
        record = parse_genbank(content)
    elif content.lstrip().startswith("ID"):
        record = parse_embl(content)
    else:
        record = SequenceRecord(name=name, sequence=sanitize_sequence(content), topology=topology)

    if payload.get("name"):
        record.name = name
    if payload.get("topology"):
        record.topology = topology
    if isinstance(payload.get("features"), list):
        feats: List[Feature] = []
        for feature in payload["features"]:
            if not isinstance(feature, dict):
                continue
            feats.append(
                Feature(
                    key=str(feature.get("key", "misc_feature")),
                    location=str(feature.get("location", "")),
                    qualifiers={k: str(v) for k, v in dict(feature.get("qualifiers", {})).items()},
                )
            )
        record.features = feats
    return record


def _decode_b64_field(value: str, label: str) -> bytes:
    if not value:
        raise ValueError(f"{label} is required")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{label} must be valid base64: {exc}") from exc


def _encode_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def apply_sequence_edit(
    record: SequenceRecord,
    op: str,
    start_1based: int,
    end_1based: int = 0,
    value: str = "",
) -> SequenceRecord:
    seq = record.sequence
    n = record.length
    if start_1based < 1 or start_1based > n + 1:
        raise ValueError("start out of bounds")
    idx = start_1based - 1

    if op == "insert":
        ins = sanitize_sequence(value)
        new_seq = seq[:idx] + ins + seq[idx:]
    elif op == "delete":
        if end_1based < start_1based or end_1based > n:
            raise ValueError("invalid delete range")
        new_seq = seq[:idx] + seq[end_1based:]
    elif op == "replace":
        if end_1based < start_1based or end_1based > n:
            raise ValueError("invalid replace range")
        rep = sanitize_sequence(value)
        new_seq = seq[:idx] + rep + seq[end_1based:]
    else:
        raise ValueError("Unsupported edit op. Use insert|delete|replace")

    return SequenceRecord(
        name=record.name,
        sequence=new_seq,
        topology=record.topology,
        molecule=record.molecule,
        features=record.features,
    )


def handle_core_endpoint(
    path: str,
    payload: Dict[str, Any],
    get_record: RecordGetter,
    collab_root: Path,
) -> Dict[str, Any] | None:
    if path == "/api/canonicalize-record":
        rec = get_record()
        return {
            "canonical_record": record_to_canonical(
                rec,
                source_format=infer_source_format(str(payload.get("content", ""))),
                source_id=str(payload.get("record_id", "")).strip(),
            )
        }

    if path == "/api/convert-record":
        target = str(payload.get("target_format", "fasta")).strip().lower()
        if isinstance(payload.get("canonical_record"), dict):
            rec = canonical_to_record(payload["canonical_record"])
            canon = payload["canonical_record"]
        else:
            rec = get_record()
            canon = record_to_canonical(
                rec,
                source_format=infer_source_format(str(payload.get("content", ""))),
                source_id=str(payload.get("record_id", "")).strip(),
            )
        if target == "fasta":
            return {"target_format": "fasta", "content": to_fasta(rec)}
        if target == "genbank":
            return {"target_format": "genbank", "content": to_genbank(rec)}
        if target == "embl":
            return {"target_format": "embl", "content": to_embl(rec)}
        if target == "json":
            return {
                "target_format": "json",
                "content": json.dumps({"payload": canonical_to_payload(canon), "canonical_record": canon}, indent=2, sort_keys=True),
            }
        if target in {"dna", "genomeforge_dna"}:
            blob = export_dna_container(
                canon,
                metadata={"name": rec.name, "topology": rec.topology, "created_by": "genomeforge"},
            )
            return {"target_format": "genomeforge_dna", "dna_base64": _encode_b64(blob), "bytes": len(blob)}
        if target == "payload":
            return {"target_format": "payload", "payload": canonical_to_payload(canon)}
        if target in {"canonical", "canonical_json"}:
            return {"target_format": "canonical", "canonical_record": canon}
        raise ValueError("Unsupported target_format. Use fasta|genbank|embl|json|dna|payload|canonical")

    if path == "/api/import-dna":
        raw = _decode_b64_field(str(payload.get("dna_base64", "")).strip(), "dna_base64")
        imported = import_dna_container(raw)
        if isinstance(imported.get("canonical_record"), dict):
            canon = imported["canonical_record"]
            rec = canonical_to_record(canon)
            doc_payload = canonical_to_payload(canon)
        elif isinstance(imported.get("payload"), dict):
            doc_payload = imported["payload"]
            rec = parse_record(doc_payload)
            canon = record_to_canonical(
                rec,
                source_format=infer_source_format(str(doc_payload.get("content", ""))),
                source_id=str(doc_payload.get("record_id", "")).strip(),
            )
        else:
            raise ValueError("DNA import did not produce canonical or payload record")
        return {
            "source": imported.get("source", "unknown"),
            "name": rec.name,
            "length": rec.length,
            "topology": rec.topology,
            "payload": doc_payload,
            "canonical_record": canon,
        }

    if path == "/api/export-dna":
        if isinstance(payload.get("canonical_record"), dict):
            rec = canonical_to_record(payload["canonical_record"])
            canon = payload["canonical_record"]
        else:
            rec = get_record()
            canon = record_to_canonical(
                rec,
                source_format=infer_source_format(str(payload.get("content", ""))),
                source_id=str(payload.get("record_id", "")).strip(),
            )
        blob = export_dna_container(
            canon,
            metadata={"name": rec.name, "topology": rec.topology, "created_by": "genomeforge"},
        )
        return {"format": "genomeforge.dna/1", "name": rec.name, "length": rec.length, "dna_base64": _encode_b64(blob), "bytes": len(blob)}

    if path == "/api/info":
        rec = get_record()
        return {
            "name": rec.name,
            "length": rec.length,
            "topology": rec.topology,
            "gc": round(rec.gc_content(), 2),
            "features": len(rec.features),
        }

    if path == "/api/primers":
        rec = get_record()
        return design_primer_pair(
            rec,
            target_start_1based=int(payload["target_start"]),
            target_end_1based=int(payload["target_end"]),
            min_len=int(payload.get("min_len", 18)),
            max_len=int(payload.get("max_len", 25)),
            window=int(payload.get("window", 80)),
            tm_min=float(payload.get("tm_min", 55.0)),
            tm_max=float(payload.get("tm_max", 68.0)),
            na_mM=float(payload.get("na_mM", 50.0)),
            primer_nM=float(payload.get("primer_nM", 250.0)),
        )

    if path == "/api/pcr":
        rec = get_record()
        return simulate_pcr(rec, forward_primer=payload["forward"], reverse_primer=payload["reverse"])

    if path == "/api/codon-optimize":
        rec = get_record()
        return optimize_coding_sequence(
            rec.sequence,
            host=str(payload.get("host", "ecoli")),
            frame=int(payload.get("frame", 1)),
            keep_stop=not bool(payload.get("drop_stop", False)),
        )

    if path == "/api/map":
        rec = get_record()
        enzymes = payload.get("enzymes", [])
        if isinstance(enzymes, str):
            enzymes = [item.strip() for item in enzymes.split(",") if item.strip()]
        return {"svg": build_svg_map(rec, enzyme_names=enzymes)}

    if path == "/api/orfs":
        rec = get_record()
        min_aa = int(payload.get("min_aa", 50))
        orfs = rec.find_orfs(min_aa_len=min_aa)
        rows = [
            {"start": start, "end": end, "frame": frame, "aa_len": len(protein), "protein_preview": protein[:40]}
            for start, end, frame, protein in orfs
        ]
        return {"count": len(rows), "orfs": rows}

    if path == "/api/motif":
        rec = get_record()
        motif = sanitize_sequence(str(payload.get("motif", "")))
        if not motif:
            raise ValueError("motif is required")
        positions = find_all_occurrences(rec.sequence, motif, circular=rec.topology == "circular")
        return {"motif": motif, "count": len(positions), "positions_1based": [pos + 1 for pos in positions]}

    if path == "/api/sequence-edit":
        rec = get_record()
        edited = apply_sequence_edit(
            rec,
            op=str(payload.get("op", "")).lower(),
            start_1based=int(payload.get("start", 1)),
            end_1based=int(payload.get("end", 0)),
            value=str(payload.get("value", "")),
        )
        return {
            "name": edited.name,
            "length": edited.length,
            "topology": edited.topology,
            "gc": round(edited.gc_content(), 2),
            "sequence": edited.sequence,
        }

    if path == "/api/mutagenesis":
        rec = get_record()
        start = int(payload.get("start", 1))
        end = int(payload.get("end", start))
        mutant = sanitize_sequence(str(payload.get("mutant", "")))
        edited = apply_sequence_edit(rec, op="replace", start_1based=start, end_1based=end, value=mutant)
        return {
            "start": start,
            "end": end,
            "mutant": mutant,
            "length": edited.length,
            "gc": round(edited.gc_content(), 2),
            "sequence": edited.sequence,
        }

    if path == "/api/batch-digest":
        records = payload.get("records", [])
        enzymes = payload.get("enzymes", [])
        if isinstance(enzymes, str):
            enzymes = [item.strip() for item in enzymes.split(",") if item.strip()]
        out_rows = []
        for item in records:
            rec = parse_record(item)
            dig = simulate_digest(rec, enzymes)
            out_rows.append(
                {
                    "name": rec.name,
                    "length": rec.length,
                    "cuts": len(dig["unique_cut_positions_1based"]),
                    "fragments_bp": dig["fragments_bp"],
                }
            )
        return {"count": len(out_rows), "results": out_rows}

    if path == "/api/workspace-create":
        members = payload.get("members", [])
        if isinstance(members, str):
            members = [item.strip() for item in members.split(",") if item.strip()]
        return create_workspace(
            collab_root,
            workspace_name=str(payload.get("workspace_name", "")).strip(),
            owner=str(payload.get("owner", "")).strip(),
            members=[str(item) for item in members],
        )

    return None
