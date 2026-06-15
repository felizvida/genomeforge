from __future__ import annotations

import json
import math
from urllib.parse import urlencode
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from genomeforge_toolkit import (
    DNA_ALPHABET,
    Feature,
    RC_TABLE,
    SequenceRecord,
    find_all_occurrences,
    iupac_hamming_distance,
    iupac_symbol_matches,
    parse_feature_interval,
)


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DB_DIR = ROOT / "reference_db"
RecordGetter = Callable[[], SequenceRecord]


def _clean_dna_string(seq: str) -> str:
    return "".join(ch for ch in str(seq).upper() if ch in DNA_ALPHABET)


def _revcomp(seq: str) -> str:
    return _clean_dna_string(seq).translate(RC_TABLE)[::-1]


def _hamming_equal_len(a: str, b: str) -> int:
    return iupac_hamming_distance(a, b)


def smith_waterman_dna(
    seq_a: str,
    seq_b: str,
    match: int = 2,
    mismatch: int = -1,
    gap: int = -2,
) -> Dict[str, Any]:
    a = _clean_dna_string(seq_a)
    b = _clean_dna_string(seq_b)
    if not a or not b:
        raise ValueError("Both sequences are required")
    m, n = len(a), len(b)
    score = [[0] * (n + 1) for _ in range(m + 1)]
    trace = [[0] * (n + 1) for _ in range(m + 1)]
    best = 0
    best_i = 0
    best_j = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s_diag = score[i - 1][j - 1] + (match if iupac_symbol_matches(a[i - 1], b[j - 1]) else mismatch)
            s_up = score[i - 1][j] + gap
            s_left = score[i][j - 1] + gap
            cell = max(0, s_diag, s_up, s_left)
            score[i][j] = cell
            if cell == 0:
                trace[i][j] = 0
            elif cell == s_diag:
                trace[i][j] = 1
            elif cell == s_up:
                trace[i][j] = 2
            else:
                trace[i][j] = 3
            if cell > best:
                best = cell
                best_i = i
                best_j = j

    i, j = best_i, best_j
    end_a = i
    end_b = j
    aa: List[str] = []
    bb: List[str] = []
    while i > 0 and j > 0 and score[i][j] > 0:
        t = trace[i][j]
        if t == 1:
            aa.append(a[i - 1])
            bb.append(b[j - 1])
            i -= 1
            j -= 1
        elif t == 2:
            aa.append(a[i - 1])
            bb.append("-")
            i -= 1
        elif t == 3:
            aa.append("-")
            bb.append(b[j - 1])
            j -= 1
        else:
            break
    start_a = i + 1
    start_b = j + 1
    aln_a = "".join(reversed(aa))
    aln_b = "".join(reversed(bb))
    aligned_columns = len(aln_a)
    matches = sum(1 for x, y in zip(aln_a, aln_b) if x != "-" and y != "-" and iupac_symbol_matches(x, y))
    aligned_a_bases = sum(1 for x in aln_a if x != "-")
    aligned_b_bases = sum(1 for y in aln_b if y != "-")
    return {
        "score": best,
        "identity_pct": round(matches / max(1, aligned_columns) * 100.0, 2),
        "aligned_a": aln_a,
        "aligned_b": aln_b,
        "alignment_length": aligned_columns,
        "aligned_a_bases": aligned_a_bases,
        "aligned_b_bases": aligned_b_bases,
        "start_a_1based": start_a,
        "end_a_1based": end_a,
        "start_b_1based": start_b,
        "end_b_1based": end_b,
    }


def _kmer_set(seq: str, k: int) -> set[str]:
    if k <= 0 or len(seq) < k:
        return set()
    return {seq[i : i + k] for i in range(len(seq) - k + 1)}


def blast_local_search(
    query_sequence: str,
    database_sequences: List[Dict[str, Any] | str],
    top_hits: int = 10,
    kmer: int = 8,
) -> Dict[str, Any]:
    query = _clean_dna_string(query_sequence)
    if not query:
        raise ValueError("query_sequence is required")
    db_rows: List[Dict[str, str]] = []
    for i, item in enumerate(database_sequences, start=1):
        if isinstance(item, dict):
            name = str(item.get("name", f"db_{i}")).strip() or f"db_{i}"
            seq = _clean_dna_string(str(item.get("sequence", "")))
        else:
            name = f"db_{i}"
            seq = _clean_dna_string(str(item))
        if seq:
            db_rows.append({"name": name, "sequence": seq})
    if not db_rows:
        raise ValueError("database_sequences must include at least one non-empty sequence")

    k = max(4, min(int(kmer), len(query)))
    qk = _kmer_set(query, k)
    hits: List[Dict[str, Any]] = []
    for row in db_rows:
        target = row["sequence"]
        tk = _kmer_set(target, k)
        inter = len(qk & tk)
        union = max(1, len(qk | tk))
        seed_jaccard = inter / union
        has_ambiguity = any(ch not in "ACGT" for ch in query + target)
        if inter == 0 and len(query) >= k and len(target) >= k and not has_ambiguity:
            continue
        aln = smith_waterman_dna(query, target, match=2, mismatch=-1, gap=-2)
        if int(aln.get("score", 0)) <= 0:
            continue
        aa = aln["aligned_a"]
        bb = aln["aligned_b"]
        aligned_columns = int(aln.get("alignment_length", len(aa)))
        matches = sum(1 for x, y in zip(aa, bb) if x != "-" and y != "-" and iupac_symbol_matches(x, y))
        aligned_query_bases = int(aln.get("aligned_a_bases", sum(1 for x in aa if x != "-")))
        aligned_target_bases = int(aln.get("aligned_b_bases", sum(1 for y in bb if y != "-")))
        query_cov = aligned_query_bases / max(1, len(query))
        target_cov = aligned_target_bases / max(1, len(target))
        score = int(aln.get("score", 0))
        evalue_proxy = math.exp(-max(0, score) / 12.0)
        hits.append(
            {
                "subject_name": row["name"],
                "subject_length": len(target),
                "score": score,
                "bitscore_proxy": round(score / 2.0, 2),
                "evalue_proxy": round(evalue_proxy, 8),
                "seed_jaccard": round(seed_jaccard, 6),
                "identity_pct": round(100.0 * matches / max(1, aligned_columns), 3),
                "query_coverage_pct": round(100.0 * query_cov, 3),
                "subject_coverage_pct": round(100.0 * target_cov, 3),
                "alignment_length": aligned_columns,
                "query_start_1based": int(aln.get("start_a_1based", 1)),
                "query_end_1based": int(aln.get("end_a_1based", len(query))),
                "subject_start_1based": int(aln.get("start_b_1based", 1)),
                "subject_end_1based": int(aln.get("end_b_1based", len(target))),
            }
        )
    hits.sort(key=lambda x: (x["score"], x["identity_pct"], x["query_coverage_pct"]), reverse=True)
    return {
        "mode": "local_blast_like",
        "query_length": len(query),
        "database_count": len(db_rows),
        "kmer": k,
        "hit_count": len(hits),
        "hits": hits[: max(1, int(top_hits))],
    }


def external_blast_launch(
    query_sequence: str,
    record_name: str = "selection",
    start_1based: int = 1,
    end_1based: int = 0,
    providers: List[str] | None = None,
    program: str = "blastn",
    database: str = "nt",
) -> Dict[str, Any]:
    query = _clean_dna_string(query_sequence)
    if not query:
        raise ValueError("query_sequence is required")
    program = str(program or "blastn").strip().lower()
    if program not in {"blastn", "blastx", "tblastx"}:
        raise ValueError("DNA launch supports blastn, blastx, or tblastx")
    database = str(database or "nt").strip() or "nt"
    selected_providers = [str(item).strip().lower() for item in (providers or ["ncbi", "wormbase"]) if str(item).strip()]
    label = "".join(ch if ch.isalnum() or ch in ("_", "-", ".") else "_" for ch in str(record_name or "selection")).strip("_")
    if not label:
        label = "selection"
    end = int(end_1based) if int(end_1based) > 0 else int(start_1based) + len(query) - 1
    fasta = f">{label}_{int(start_1based)}_{end}\n{query}\n"
    launches: List[Dict[str, Any]] = []

    if "ncbi" in selected_providers:
        search_params = {
            "PAGE_TYPE": "BlastSearch",
            "PROGRAM": program,
            "BLAST_PROGRAMS": program,
            "QUERY": fasta,
            "DATABASE": database,
        }
        submit_params = {"CMD": "Put", "PROGRAM": program, "DATABASE": database, "QUERY": fasta}
        launches.append(
            {
                "provider": "NCBI BLAST",
                "kind": "prefilled_search_page",
                "url": "https://blast.ncbi.nlm.nih.gov/Blast.cgi?" + urlencode(search_params),
                "submit_url": "https://blast.ncbi.nlm.nih.gov/Blast.cgi?" + urlencode(submit_params),
                "program": program,
                "database": database,
                "prefill_supported": True,
            }
        )

    if "wormbase" in selected_providers:
        launches.append(
            {
                "provider": "WormBase BLAST/BLAT",
                "kind": "tool_page_with_copyable_fasta",
                "url": "https://wormbase.org/tools/blast_blat",
                "program": program,
                "database": "WormBase genome/protein collections",
                "prefill_supported": False,
                "note": "Open WormBase BLAST/BLAT, then paste the FASTA payload from copy_fasta.",
            }
        )

    if "wormbase_parasite" in selected_providers or "parasite" in selected_providers:
        launches.append(
            {
                "provider": "WormBase ParaSite BLAST",
                "kind": "tool_page_with_copyable_fasta",
                "url": "https://parasite.wormbase.org/Tools/Blast",
                "program": program,
                "database": "WormBase ParaSite genomes",
                "prefill_supported": False,
                "note": "Open WormBase ParaSite BLAST, then paste the FASTA payload from copy_fasta.",
            }
        )

    if not launches:
        raise ValueError("No supported providers requested")
    return {
        "query_length": len(query),
        "record_name": label,
        "selection_start_1based": int(start_1based),
        "selection_end_1based": end,
        "copy_fasta": fasta,
        "launches": launches,
    }


def _features_to_dict(features: List[Feature]) -> List[Dict[str, Any]]:
    return [{"key": f.key, "location": f.location, "qualifiers": dict(f.qualifiers)} for f in features]


def _payload_features_to_dict(features: Any) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not isinstance(features, list):
        return rows
    for feature in features:
        if isinstance(feature, Feature):
            rows.append({"key": feature.key, "location": feature.location, "qualifiers": dict(feature.qualifiers)})
        elif isinstance(feature, dict):
            qualifiers = feature.get("qualifiers", {})
            rows.append(
                {
                    "key": str(feature.get("key", "misc_feature") or "misc_feature"),
                    "location": str(feature.get("location", "")),
                    "qualifiers": dict(qualifiers) if isinstance(qualifiers, dict) else {"label": str(qualifiers)},
                }
            )
    return rows


def _feature_label(feature: Dict[str, Any]) -> str:
    qualifiers = feature.get("qualifiers", {})
    if isinstance(qualifiers, dict):
        for key in ("label", "gene", "product", "note"):
            if str(qualifiers.get(key, "")).strip():
                return str(qualifiers[key]).strip()
    return str(feature.get("key", "feature"))


def _alignment_ref_to_target_map(alignment: Dict[str, Any]) -> Dict[int, int]:
    target_pos = int(alignment.get("start_a_1based", 1)) - 1
    ref_pos = int(alignment.get("start_b_1based", 1)) - 1
    mapping: Dict[int, int] = {}
    for target_base, ref_base in zip(str(alignment.get("aligned_a", "")), str(alignment.get("aligned_b", ""))):
        if target_base != "-":
            target_pos += 1
        if ref_base != "-":
            ref_pos += 1
        if target_base != "-" and ref_base != "-":
            mapping[ref_pos] = target_pos
    return mapping


def _feature_bounds_for_orientation(feature: Dict[str, Any], reference_length: int, orientation: str) -> tuple[int, int] | None:
    bounds = parse_feature_interval(str(feature.get("location", "")))
    if not bounds:
        return None
    start, end = bounds
    start = max(1, min(reference_length, start))
    end = max(1, min(reference_length, end))
    if start > end:
        start, end = end, start
    if orientation == "-":
        return reference_length - end + 1, reference_length - start + 1
    return start, end


def _transferred_location(start: int, end: int, orientation: str, source_location: str) -> tuple[str, str]:
    source_is_complement = "complement" in source_location.lower()
    target_is_complement = (orientation == "-") ^ source_is_complement
    location = f"{start}..{end}"
    return (f"complement({location})" if target_is_complement else location), ("-" if target_is_complement else "+")


def _reference_records_from_db(db_name: str) -> List[Dict[str, Any]]:
    if not db_name:
        return []
    doc = load_reference_db(db_name)
    records: List[Dict[str, Any]] = []
    for element in doc.get("elements", []):
        sequence = _clean_dna_string(str(element.get("sequence", "")))
        if not sequence:
            continue
        label = str(element.get("label", "reference element"))
        key = str(element.get("type", "misc_feature") or "misc_feature")
        records.append(
            {
                "name": label,
                "sequence": sequence,
                "features": [
                    {
                        "key": key,
                        "location": f"1..{len(sequence)}",
                        "qualifiers": {"label": label, "source": f"reference_db:{db_name}"},
                    }
                ],
            }
        )
    return records


def annotation_transfer_by_similarity(
    target_record: SequenceRecord,
    reference_records: List[Dict[str, Any]],
    min_identity_pct: float = 85.0,
    min_feature_coverage_pct: float = 70.0,
    add_features: bool = False,
    max_features: int = 200,
) -> Dict[str, Any]:
    target = _clean_dna_string(target_record.sequence)
    if not target:
        raise ValueError("target record sequence is required")
    if not reference_records:
        raise ValueError("reference_records or db_name is required")

    transferred: List[Dict[str, Any]] = []
    reference_summaries: List[Dict[str, Any]] = []
    original_feature_count = len(target_record.features)
    existing = {
        (feature.key, feature.location, str(feature.qualifiers.get("label", "")))
        for feature in target_record.features
    }
    for index, raw_ref in enumerate(reference_records, start=1):
        if not isinstance(raw_ref, dict):
            continue
        ref_name = str(raw_ref.get("name", raw_ref.get("label", f"reference_{index}")) or f"reference_{index}")
        ref_seq = _clean_dna_string(str(raw_ref.get("sequence", "")))
        features = _payload_features_to_dict(raw_ref.get("features", []))
        if not ref_seq or not features:
            reference_summaries.append(
                {
                    "reference_name": ref_name,
                    "status": "skipped",
                    "reason": "missing sequence or features",
                }
            )
            continue

        candidates = []
        for orientation, oriented_seq in (("+", ref_seq), ("-", _revcomp(ref_seq))):
            alignment = smith_waterman_dna(target, oriented_seq)
            candidates.append((int(alignment.get("score", 0)), orientation, alignment))
        _score, orientation, alignment = max(candidates, key=lambda item: item[0])
        identity_pct = float(alignment.get("identity_pct", 0.0))
        reference_coverage_pct = round(100.0 * int(alignment.get("aligned_b_bases", 0)) / max(1, len(ref_seq)), 2)
        target_coverage_pct = round(100.0 * int(alignment.get("aligned_a_bases", 0)) / max(1, len(target)), 2)
        mapping = _alignment_ref_to_target_map(alignment)
        accepted = 0
        rejected = 0
        for feature in features:
            if len(transferred) >= max(1, int(max_features)):
                break
            oriented_bounds = _feature_bounds_for_orientation(feature, len(ref_seq), orientation)
            if not oriented_bounds:
                rejected += 1
                continue
            f_start, f_end = oriented_bounds
            feature_len = max(1, f_end - f_start + 1)
            mapped_positions = [mapping[pos] for pos in range(f_start, f_end + 1) if pos in mapping]
            feature_coverage_pct = round(100.0 * len(mapped_positions) / feature_len, 2)
            if not mapped_positions or identity_pct < float(min_identity_pct) or feature_coverage_pct < float(min_feature_coverage_pct):
                rejected += 1
                continue

            target_start = min(mapped_positions)
            target_end = max(mapped_positions)
            location, strand = _transferred_location(target_start, target_end, orientation, str(feature.get("location", "")))
            key = str(feature.get("key", "misc_feature") or "misc_feature")
            label = _feature_label(feature)
            qualifiers = feature.get("qualifiers", {})
            out_qualifiers = dict(qualifiers) if isinstance(qualifiers, dict) else {"label": label}
            out_qualifiers.update(
                {
                    "label": label,
                    "source": "similarity_annotation_transfer",
                    "transferred_from": ref_name,
                    "identity_pct": f"{identity_pct:.2f}",
                    "feature_coverage_pct": f"{feature_coverage_pct:.2f}",
                }
            )
            row = {
                "source_record": ref_name,
                "key": key,
                "label": label,
                "reference_location": str(feature.get("location", "")),
                "target_location": location,
                "start_1based": target_start,
                "end_1based": target_end,
                "strand": strand,
                "orientation": orientation,
                "identity_pct": round(identity_pct, 2),
                "reference_coverage_pct": reference_coverage_pct,
                "feature_coverage_pct": feature_coverage_pct,
            }
            transferred.append(row)
            accepted += 1
            marker = (key, location, label)
            if add_features and marker not in existing:
                target_record.features.append(Feature(key=key, location=location, qualifiers=out_qualifiers))
                existing.add(marker)
        reference_summaries.append(
            {
                "reference_name": ref_name,
                "reference_length": len(ref_seq),
                "feature_count": len(features),
                "orientation": orientation,
                "identity_pct": round(identity_pct, 2),
                "reference_coverage_pct": reference_coverage_pct,
                "target_coverage_pct": target_coverage_pct,
                "accepted_features": accepted,
                "rejected_features": rejected,
            }
        )

    return {
        "mode": "similarity_annotation_transfer",
        "target_name": target_record.name,
        "target_length": len(target),
        "reference_count": len(reference_records),
        "min_identity_pct": float(min_identity_pct),
        "min_feature_coverage_pct": float(min_feature_coverage_pct),
        "transferred_count": len(transferred),
        "transferred_features": transferred,
        "features_added": len(target_record.features) - original_feature_count,
        "feature_count": len(target_record.features),
        "features": _features_to_dict(target_record.features),
        "references": reference_summaries,
        "truncated": len(transferred) >= max(1, int(max_features)),
    }


def reference_db_path(name: str) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid reference db name")
    REFERENCE_DB_DIR.mkdir(parents=True, exist_ok=True)
    return REFERENCE_DB_DIR / f"{safe}.json"


def save_reference_db(name: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    path = reference_db_path(name)
    cleaned = []
    for element in elements:
        if not isinstance(element, dict):
            continue
        seq = _clean_dna_string(str(element.get("sequence", "")))
        if not seq:
            continue
        cleaned.append(
            {
                "label": str(element.get("label", "element")).strip() or "element",
                "type": str(element.get("type", "misc_feature")).strip() or "misc_feature",
                "sequence": seq,
                "max_mismatch": max(0, min(3, int(element.get("max_mismatch", 0)))),
            }
        )
    doc = {"name": name, "updated_at": datetime.now(timezone.utc).isoformat(), "elements": cleaned}
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"saved": True, "db_name": name, "count": len(cleaned)}


def list_reference_dbs() -> Dict[str, Any]:
    REFERENCE_DB_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(REFERENCE_DB_DIR.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "db_name": path.stem,
                    "path": str(path),
                    "updated_at": str(doc.get("updated_at", "")),
                    "count": len(doc.get("elements", [])),
                }
            )
        except Exception:  # noqa: BLE001
            continue
    return {"count": len(rows), "databases": rows}


def load_reference_db(name: str) -> Dict[str, Any]:
    path = reference_db_path(name)
    if not path.exists():
        raise ValueError("Reference DB not found")
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {"db_name": name, "updated_at": doc.get("updated_at", ""), "elements": doc.get("elements", [])}


def _seq_with_mismatches(seq: str, motif: str, max_mismatch: int) -> List[Tuple[int, int]]:
    if not motif:
        return []
    out: List[Tuple[int, int]] = []
    m = len(motif)
    if len(seq) < m:
        return out
    for i in range(len(seq) - m + 1):
        mismatches = _hamming_equal_len(seq[i : i + m], motif)
        if mismatches <= max_mismatch:
            out.append((i, mismatches))
    return out


def reference_scan(record: SequenceRecord, db_name: str, add_features: bool = False) -> Dict[str, Any]:
    doc = load_reference_db(db_name)
    seq = record.sequence
    hits: List[Dict[str, Any]] = []
    for i, element in enumerate(doc.get("elements", [])):
        motif = _clean_dna_string(str(element.get("sequence", "")))
        if not motif:
            continue
        max_mismatch = max(0, min(3, int(element.get("max_mismatch", 0))))
        direct = _seq_with_mismatches(seq, motif, max_mismatch)
        rc = _revcomp(motif)
        reverse_hits = _seq_with_mismatches(seq, rc, max_mismatch) if rc != motif else []
        for pos0, mismatches in direct:
            hits.append(
                {
                    "element_index": i,
                    "label": str(element.get("label", "element")),
                    "type": str(element.get("type", "misc_feature")),
                    "start_1based": pos0 + 1,
                    "end_1based": pos0 + len(motif),
                    "strand": "+",
                    "mismatch_count": mismatches,
                }
            )
        for pos0, mismatches in reverse_hits:
            hits.append(
                {
                    "element_index": i,
                    "label": str(element.get("label", "element")),
                    "type": str(element.get("type", "misc_feature")),
                    "start_1based": pos0 + 1,
                    "end_1based": pos0 + len(motif),
                    "strand": "-",
                    "mismatch_count": mismatches,
                }
            )
    hits.sort(key=lambda x: (x["mismatch_count"], x["start_1based"]))
    added = 0
    if add_features and hits:
        for hit in hits:
            key = str(hit["type"] or "misc_feature")
            if key == "rbs":
                key = "RBS"
            loc = f"{hit['start_1based']}..{hit['end_1based']}"
            if hit["strand"] == "-":
                loc = f"complement({loc})"
            record.features.append(
                Feature(
                    key=key,
                    location=loc,
                    qualifiers={"label": hit["label"], "source": f"reference_db:{db_name}", "mismatch": str(hit["mismatch_count"])},
                )
            )
            added += 1
    return {
        "db_name": db_name,
        "hit_count": len(hits),
        "hits": hits[:2000],
        "features_added": added,
        "feature_count": len(record.features),
        "features": _features_to_dict(record.features),
    }


def design_sirna_candidates(sequence: str, min_len: int = 19, max_len: int = 21, top_n: int = 40) -> Dict[str, Any]:
    seq = _clean_dna_string(sequence)
    if not seq:
        raise ValueError("sequence is required")
    min_len = max(17, int(min_len))
    max_len = max(min_len, min(24, int(max_len)))
    candidates: List[Dict[str, Any]] = []
    for k in range(min_len, max_len + 1):
        for i in range(0, len(seq) - k + 1):
            target = seq[i : i + k]
            gc = 100.0 * (target.count("G") + target.count("C")) / max(1, k)
            score = 100.0
            score -= abs(gc - 45.0) * 1.2
            if target[0] == "G":
                score -= 4.0
            if "AAAA" in target or "TTTT" in target or "CCCC" in target or "GGGG" in target:
                score -= 15.0
            if target.count("N") > 0:
                score -= 30.0
            antisense = _revcomp(target).replace("T", "U")
            sense_rna = target.replace("T", "U")
            candidates.append(
                {
                    "start_1based": i + 1,
                    "end_1based": i + k,
                    "length": k,
                    "target_dna": target,
                    "sense_rna": sense_rna,
                    "antisense_rna": antisense,
                    "gc_pct": round(gc, 2),
                    "score": round(max(0.0, min(100.0, score)), 2),
                }
            )
    candidates.sort(key=lambda x: (x["score"], -abs(x["gc_pct"] - 45.0)), reverse=True)
    return {"sequence_length": len(seq), "candidate_count": len(candidates), "candidates": candidates[: max(1, int(top_n))]}


def map_sirna_sites(sequence: str, sirna_sequence: str) -> Dict[str, Any]:
    seq = _clean_dna_string(sequence)
    target = _clean_dna_string(str(sirna_sequence).upper().replace("U", "T"))
    if not seq or not target:
        raise ValueError("sequence and sirna_sequence are required")
    rc = _revcomp(target)
    plus = find_all_occurrences(seq, target, circular=False)
    minus = find_all_occurrences(seq, rc, circular=False)
    hits = []
    for pos in plus:
        hits.append({"start_1based": pos + 1, "end_1based": pos + len(target), "strand": "+", "match": target})
    for pos in minus:
        hits.append({"start_1based": pos + 1, "end_1based": pos + len(target), "strand": "-", "match": rc})
    hits.sort(key=lambda x: (x["start_1based"], x["strand"]))
    return {"sirna_sequence": target, "hit_count": len(hits), "hits": hits}


def handle_search_reference_endpoint(path: str, payload: Dict[str, Any], get_record: RecordGetter) -> Dict[str, Any] | None:
    if path == "/api/blast-launch":
        record = get_record()
        raw_query = str(payload.get("query_sequence", payload.get("query", ""))).strip()
        start = max(1, int(payload.get("start", payload.get("selection_start", 1))))
        end = int(payload.get("end", payload.get("selection_end", 0)))
        if raw_query:
            query = raw_query
            launch_start = start
            launch_end = end if end > 0 else start + len(_clean_dna_string(raw_query)) - 1
        else:
            if end <= 0:
                end = record.length
            start = min(start, record.length)
            end = max(start, min(end, record.length))
            query = record.sequence[start - 1 : end]
            launch_start = start
            launch_end = end
        providers = payload.get("providers", ["ncbi", "wormbase"])
        if isinstance(providers, str):
            providers = [item.strip() for item in providers.split(",") if item.strip()]
        return external_blast_launch(
            query,
            record_name=str(payload.get("record_name", record.name)),
            start_1based=launch_start,
            end_1based=launch_end,
            providers=[str(item) for item in providers],
            program=str(payload.get("program", "blastn")),
            database=str(payload.get("database", "nt")),
        )

    if path == "/api/blast-search":
        query = str(payload.get("query_sequence", payload.get("query", "")))
        if not query.strip():
            query = get_record().sequence
        database = payload.get("database_sequences", [])
        if isinstance(database, str):
            database = [{"name": f"db_{i+1}", "sequence": line.strip()} for i, line in enumerate(database.splitlines()) if line.strip()]
        if not database:
            record = get_record()
            database = [{"name": record.name, "sequence": record.sequence}]
        return blast_local_search(
            query_sequence=query,
            database_sequences=list(database),
            top_hits=int(payload.get("top_hits", 10)),
            kmer=int(payload.get("kmer", 8)),
        )

    if path == "/api/reference-db-save":
        name = str(payload.get("db_name", "")).strip()
        elements = payload.get("elements", [])
        if isinstance(elements, str):
            elements = json.loads(elements)
        return save_reference_db(name, [dict(x) for x in elements if isinstance(x, dict)])

    if path == "/api/reference-db-list":
        return list_reference_dbs()

    if path == "/api/reference-db-load":
        return load_reference_db(str(payload.get("db_name", "")).strip())

    if path == "/api/reference-scan":
        return reference_scan(
            get_record(),
            db_name=str(payload.get("db_name", "")).strip(),
            add_features=bool(payload.get("add_features", False)),
        )

    if path == "/api/annotation-transfer":
        reference_records = payload.get("reference_records", payload.get("references", []))
        if isinstance(reference_records, str):
            reference_records = json.loads(reference_records)
        refs = [dict(item) for item in reference_records if isinstance(item, dict)] if isinstance(reference_records, list) else []
        db_name = str(payload.get("db_name", "")).strip()
        if db_name:
            try:
                refs.extend(_reference_records_from_db(db_name))
            except ValueError:
                if not refs:
                    raise
        return annotation_transfer_by_similarity(
            get_record(),
            refs,
            min_identity_pct=float(payload.get("min_identity_pct", 85.0)),
            min_feature_coverage_pct=float(payload.get("min_feature_coverage_pct", 70.0)),
            add_features=bool(payload.get("add_features", False)),
            max_features=int(payload.get("max_features", 200)),
        )

    if path == "/api/sirna-design":
        sequence = str(payload.get("sequence", ""))
        if not sequence.strip():
            sequence = get_record().sequence
        return design_sirna_candidates(
            sequence=sequence,
            min_len=int(payload.get("min_len", 19)),
            max_len=int(payload.get("max_len", 21)),
            top_n=int(payload.get("top_n", 40)),
        )

    if path == "/api/sirna-map":
        sequence = str(payload.get("sequence", ""))
        if not sequence.strip():
            sequence = get_record().sequence
        return map_sirna_sites(sequence=sequence, sirna_sequence=str(payload.get("sirna_sequence", "")))

    return None
