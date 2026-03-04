from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from snapgene_like import Feature, SequenceRecord, sanitize_sequence


CANONICAL_SCHEMA_VERSION = "1.0.0"


def infer_source_format(content: str) -> str:
    c = str(content or "").lstrip()
    if not c:
        return "unknown"
    if c.startswith(">"):
        return "fasta"
    if c.startswith("LOCUS"):
        return "genbank"
    if c.startswith("ID"):
        return "embl"
    return "raw_dna"


@dataclass
class CanonicalFeature:
    id: str
    key: str
    location: str
    start_1based: int
    end_1based: int
    strand: int
    qualifiers: Dict[str, str] = field(default_factory=dict)


@dataclass
class CanonicalRecord:
    schema: str
    created_at: str
    source_format: str
    record_id: str
    name: str
    molecule: str
    topology: str
    length: int
    sequence: str
    gc_pct: float
    features: List[CanonicalFeature] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    checksum_sha256: str = ""


def _feature_bounds(loc: str) -> tuple[int, int, int]:
    s = str(loc or "")
    strand = -1 if "complement" in s.lower() else 1
    nums = [int(x) for x in "".join(ch if ch.isdigit() else " " for ch in s).split()]
    if len(nums) < 2:
        return 0, 0, strand
    a, b = nums[0], nums[-1]
    if a > b:
        a, b = b, a
    return a, b, strand


def _record_checksum(name: str, topology: str, seq: str, features: List[Dict[str, Any]]) -> str:
    payload = {
        "name": name,
        "topology": topology,
        "sequence": seq,
        "features": features,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def record_to_canonical(record: SequenceRecord, source_format: str = "unknown", source_id: str = "") -> Dict[str, Any]:
    feats: List[CanonicalFeature] = []
    feat_rows = []
    for i, f in enumerate(record.features):
        a, b, strand = _feature_bounds(f.location)
        fid = f"feat_{i+1}"
        cf = CanonicalFeature(
            id=fid,
            key=str(f.key),
            location=str(f.location),
            start_1based=a,
            end_1based=b,
            strand=strand,
            qualifiers={str(k): str(v) for k, v in dict(f.qualifiers).items()},
        )
        feats.append(cf)
        feat_rows.append(asdict(cf))

    seq = sanitize_sequence(record.sequence)
    checksum = _record_checksum(record.name, record.topology, seq, feat_rows)
    out = CanonicalRecord(
        schema=CANONICAL_SCHEMA_VERSION,
        created_at=datetime.now(timezone.utc).isoformat(),
        source_format=source_format,
        record_id=source_id or checksum[:16],
        name=str(record.name),
        molecule=str(record.molecule),
        topology=str(record.topology),
        length=len(seq),
        sequence=seq,
        gc_pct=round(record.gc_content(), 4),
        features=feats,
        provenance={"generator": "genomeforge", "source_id": source_id or ""},
        checksum_sha256=checksum,
    )
    data = asdict(out)
    data["features"] = feat_rows
    return data


def canonical_to_record(canonical: Dict[str, Any]) -> SequenceRecord:
    seq = sanitize_sequence(str(canonical.get("sequence", "")))
    if not seq:
        raise ValueError("canonical_record.sequence is required")
    name = str(canonical.get("name", "Untitled")).strip() or "Untitled"
    topology = str(canonical.get("topology", "linear")).strip().lower()
    if topology not in {"linear", "circular"}:
        topology = "linear"
    molecule = str(canonical.get("molecule", "DNA")).strip() or "DNA"
    feats_in = canonical.get("features", [])
    feats: List[Feature] = []
    for row in feats_in if isinstance(feats_in, list) else []:
        if not isinstance(row, dict):
            continue
        feats.append(
            Feature(
                key=str(row.get("key", "misc_feature")),
                location=str(row.get("location", "")),
                qualifiers={str(k): str(v) for k, v in dict(row.get("qualifiers", {})).items()},
            )
        )
    return SequenceRecord(name=name, sequence=seq, topology=topology, molecule=molecule, features=feats)


def canonical_to_payload(canonical: Dict[str, Any]) -> Dict[str, Any]:
    rec = canonical_to_record(canonical)
    return {
        "name": rec.name,
        "topology": rec.topology,
        "content": f">{rec.name}\n{rec.sequence}",
        "features": [{"key": f.key, "location": f.location, "qualifiers": dict(f.qualifiers)} for f in rec.features],
        "canonical_record": canonical,
    }

