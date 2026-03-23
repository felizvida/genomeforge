from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

from genomeforge_toolkit import (
    ENZYMES,
    Feature,
    SequenceRecord,
    find_all_occurrences,
    primer_quality,
    sanitize_sequence,
    seq_tm_nn,
    simulate_digest,
    simulate_pcr,
)


ROOT = Path(__file__).resolve().parents[1]
ENZYME_SET_DIR = ROOT / "enzyme_sets"
ANNOT_DB_DIR = ROOT / "annotation_db"
RecordGetter = Callable[[], SequenceRecord]

ENZYME_META: Dict[str, Dict[str, Any]] = {
    "EcoRI": {"site": "GAATTC", "cut_offset": 1, "type": "Type II", "methylation_blocked_by": ["GAATTC"]},
    "BamHI": {"site": "GGATCC", "cut_offset": 1, "type": "Type II", "methylation_blocked_by": ["GGATCC"]},
    "HindIII": {"site": "AAGCTT", "cut_offset": 1, "type": "Type II", "methylation_blocked_by": []},
    "XhoI": {"site": "CTCGAG", "cut_offset": 1, "type": "Type II", "methylation_blocked_by": []},
    "XbaI": {"site": "TCTAGA", "cut_offset": 1, "type": "Type II", "methylation_blocked_by": []},
    "SpeI": {"site": "ACTAGT", "cut_offset": 1, "type": "Type II", "methylation_blocked_by": []},
    "PstI": {"site": "CTGCAG", "cut_offset": 5, "type": "Type II", "methylation_blocked_by": []},
    "NotI": {"site": "GCGGCCGC", "cut_offset": 2, "type": "Type II", "methylation_blocked_by": []},
    "NheI": {"site": "GCTAGC", "cut_offset": 1, "type": "Type II", "methylation_blocked_by": []},
    "KpnI": {"site": "GGTACC", "cut_offset": 5, "type": "Type II", "methylation_blocked_by": []},
    "BsaI": {"site": "GGTCTC", "cut_offset": 1, "type": "Type IIS", "methylation_blocked_by": []},
}

BUILTIN_ENZYME_SETS: Dict[str, List[str]] = {
    "common_6cutter": ["EcoRI", "BamHI", "HindIII", "XhoI", "XbaI", "PstI"],
    "cloning_core": ["EcoRI", "BamHI", "HindIII", "XhoI", "XbaI", "SpeI", "NheI", "KpnI"],
    "rare_cutters": ["NotI"],
    "golden_gate": ["BsaI"],
}

ANNOTATION_PATTERNS: List[Dict[str, str]] = [
    {"label": "Bacterial -10 box", "type": "promoter", "motif": "TATAAT"},
    {"label": "Bacterial -35 box", "type": "promoter", "motif": "TTGACA"},
    {"label": "Shine-Dalgarno", "type": "rbs", "motif": "AGGAGG"},
    {"label": "FLAG tag", "type": "tag", "motif": "GACTACAAGGACGACGATGACAAG"},
    {"label": "His6 tag", "type": "tag", "motif": "CATCACCATCACCATCAC"},
    {"label": "T7 promoter", "type": "promoter", "motif": "TAATACGACTCACTATAGGG"},
]

GEL_MARKER_SETS: Dict[str, List[int]] = {
    "1kb_plus": [20000, 10000, 8000, 6000, 5000, 4000, 3000, 2000, 1500, 1000, 700, 500, 300, 100],
    "100bp": [3000, 2000, 1500, 1200, 1000, 900, 800, 700, 600, 500, 400, 300, 200, 100],
    "ultra_low": [1000, 900, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 75, 50, 25],
    "high_range": [50000, 40000, 30000, 20000, 15000, 10000, 8000, 6000, 5000, 4000, 3000, 2000, 1000],
}


def _parse_plain_sequence(seq: str) -> str:
    return sanitize_sequence(seq)


def digest_with_methylation(
    record: SequenceRecord,
    enzymes: List[str],
    methylated_motifs: List[str],
) -> Dict[str, Any]:
    raw = simulate_digest(record, enzymes)
    methyl = [_parse_plain_sequence(motif) for motif in methylated_motifs if str(motif).strip()]
    blocked_positions = set()
    blocked_details: List[Dict[str, Any]] = []
    for enzyme in enzymes:
        site = ENZYME_META.get(enzyme, {}).get("site")
        if site and site in methyl:
            positions = find_all_occurrences(record.sequence, site, circular=record.topology == "circular")
            offset = ENZYME_META.get(enzyme, {}).get("cut_offset", 0)
            for pos in positions:
                cut_1based = ((pos + offset) % record.length) + 1 if record.topology == "circular" else (pos + offset + 1)
                blocked_positions.add(cut_1based)
                blocked_details.append({"enzyme": enzyme, "site": site, "position_1based": cut_1based})

    cuts = [cut for cut in raw["cuts"] if cut["position_1based"] not in blocked_positions]
    unique_cut_positions = sorted({cut["position_1based"] for cut in cuts})
    if not unique_cut_positions:
        fragments = [record.length]
    elif record.topology == "circular":
        if len(unique_cut_positions) == 1:
            fragments = [record.length]
        else:
            zero_based = [pos - 1 for pos in unique_cut_positions]
            fragments = [(zero_based[(i + 1) % len(zero_based)] - zero_based[i]) % record.length for i in range(len(zero_based))]
    else:
        bounds = [1] + unique_cut_positions + [record.length + 1]
        fragments = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]

    return {
        "topology": record.topology,
        "methylated_motifs": methyl,
        "blocked_cuts": blocked_details,
        "cuts": cuts,
        "unique_cut_positions_1based": unique_cut_positions,
        "fragments_bp": sorted([fragment for fragment in fragments if fragment > 0], reverse=True),
    }


def _hamming(a: str, b: str) -> int:
    if len(a) != len(b):
        return max(len(a), len(b))
    return sum(1 for left, right in zip(a, b) if left != right)


def star_activity_scan(
    record: SequenceRecord,
    enzymes: List[str],
    star_activity_level: float = 0.0,
    include_star_cuts: bool = False,
) -> Dict[str, Any]:
    seq = record.sequence
    n = len(seq)
    circular = record.topology == "circular"
    level = max(0.0, min(1.0, float(star_activity_level)))
    if level < 0.15:
        max_mismatch = 0
    elif level < 0.7:
        max_mismatch = 1
    else:
        max_mismatch = 2

    exact = simulate_digest(record, enzymes)
    star_hits: List[Dict[str, Any]] = []
    star_cut_points = []
    for enzyme in enzymes:
        if enzyme not in ENZYMES:
            continue
        site, offset = ENZYMES[enzyme]
        m = len(site)
        scan_seq = seq + (seq[: m - 1] if circular else "")
        limit = n if circular else n - m + 1
        for i in range(max(0, limit)):
            motif = scan_seq[i : i + m]
            if len(motif) != m:
                continue
            mismatches = _hamming(motif, site)
            if mismatches == 0:
                continue
            if mismatches <= max_mismatch:
                cut = ((i + offset) % n) + 1 if circular else (i + offset + 1)
                star_hits.append(
                    {
                        "enzyme": enzyme,
                        "site": site,
                        "matched": motif,
                        "mismatches": mismatches,
                        "site_start_1based": i + 1,
                        "cut_position_1based": cut,
                    }
                )
                star_cut_points.append(cut)

    star_hits.sort(key=lambda hit: (hit["mismatches"], hit["cut_position_1based"]))
    out = {
        "star_activity_level": level,
        "max_mismatch": max_mismatch,
        "exact_digest": exact,
        "star_hits": star_hits,
        "star_hit_count": len(star_hits),
    }
    if include_star_cuts:
        cuts = list(exact["cuts"]) + [{"enzyme": "STAR", "position_1based": pos} for pos in star_cut_points]
        unique = sorted({cut["position_1based"] for cut in cuts})
        if not unique:
            fragments = [record.length]
        elif record.topology == "circular":
            if len(unique) == 1:
                fragments = [record.length]
            else:
                zero_based = [pos - 1 for pos in unique]
                fragments = [(zero_based[(i + 1) % len(zero_based)] - zero_based[i]) % record.length for i in range(len(zero_based))]
        else:
            bounds = [1] + unique + [record.length + 1]
            fragments = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]
        out["digest_with_star"] = {
            "cuts": sorted(cuts, key=lambda cut: cut["position_1based"]),
            "unique_cut_positions_1based": unique,
            "fragments_bp": sorted([fragment for fragment in fragments if fragment > 0], reverse=True),
        }
    return out


def primer_diagnostics(
    forward: str,
    reverse: str,
    na_mM: float = 50.0,
    primer_nM: float = 250.0,
) -> Dict[str, Any]:
    from genomeforge_toolkit import end_complement_run, max_complement_run

    forward_seq = sanitize_sequence(forward)
    reverse_seq = sanitize_sequence(reverse)
    forward_quality = primer_quality(forward_seq)
    reverse_quality = primer_quality(reverse_seq)
    forward_quality["tm_nn"] = seq_tm_nn(forward_seq, na_mM=na_mM, primer_nM=primer_nM)
    reverse_quality["tm_nn"] = seq_tm_nn(reverse_seq, na_mM=na_mM, primer_nM=primer_nM)
    heterodimer = max_complement_run(forward_seq, reverse_seq)
    heterodimer_end = end_complement_run(forward_seq, reverse_seq)
    risk_flags = []
    if heterodimer_end >= 5:
        risk_flags.append("high_3prime_heterodimer")
    if forward_quality["hairpin_stem"] >= 6 or reverse_quality["hairpin_stem"] >= 6:
        risk_flags.append("strong_hairpin")
    if abs(forward_quality["tm_nn"] - reverse_quality["tm_nn"]) > 5:
        risk_flags.append("tm_imbalance")
    return {
        "conditions": {"na_mM": na_mM, "primer_nM": primer_nM},
        "forward": forward_quality,
        "reverse": reverse_quality,
        "pair": {
            "heterodimer_run": heterodimer,
            "heterodimer_3prime_run": heterodimer_end,
            "tm_delta": round(abs(float(forward_quality["tm_nn"]) - float(reverse_quality["tm_nn"])), 2),
            "predicted_risk_flags": risk_flags,
        },
    }


def auto_annotate(record: SequenceRecord) -> Dict[str, Any]:
    circular = record.topology == "circular"
    rows: List[Dict[str, Any]] = []
    for pattern in ANNOTATION_PATTERNS:
        motif = pattern["motif"]
        hits = find_all_occurrences(record.sequence, motif, circular=circular)
        for hit in hits:
            start = hit + 1
            end = hit + len(motif)
            if end > record.length and circular:
                end -= record.length
            rows.append(
                {
                    "label": pattern["label"],
                    "type": pattern["type"],
                    "motif": motif,
                    "start_1based": start,
                    "end_1based": end,
                }
            )
    for idx, (start, end, frame, protein) in enumerate(record.find_orfs(min_aa_len=40), start=1):
        rows.append(
            {
                "label": f"Auto_CDS_{idx}",
                "type": "CDS",
                "motif": "ORF",
                "start_1based": start,
                "end_1based": end,
                "frame": frame,
                "aa_len": len(protein),
            }
        )
    rows.sort(key=lambda row: row["start_1based"])
    return {"count": len(rows), "annotations": rows}


def features_to_dict(features: List[Feature]) -> List[Dict[str, Any]]:
    return [{"key": feature.key, "location": feature.location, "qualifiers": dict(feature.qualifiers)} for feature in features]


def enzyme_set_path(name: str) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid enzyme set name")
    ENZYME_SET_DIR.mkdir(parents=True, exist_ok=True)
    return ENZYME_SET_DIR / f"{safe}.json"


def save_enzyme_set(name: str, enzymes: List[str], notes: str = "") -> Dict[str, Any]:
    clean = [enzyme for enzyme in [str(item).strip() for item in enzymes] if enzyme]
    unknown = [enzyme for enzyme in clean if enzyme not in ENZYME_META and enzyme not in ENZYMES]
    if unknown:
        raise ValueError(f"Unknown enzymes in set: {', '.join(sorted(set(unknown)))}")
    path = enzyme_set_path(name)
    doc = {
        "name": name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "enzymes": sorted(set(clean)),
        "notes": notes,
    }
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"saved": True, "name": name, "count": len(doc["enzymes"]), "path": str(path)}


def list_enzyme_sets() -> Dict[str, Any]:
    ENZYME_SET_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(ENZYME_SET_DIR.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "name": doc.get("name", path.stem),
                    "updated_at": doc.get("updated_at", ""),
                    "count": len(doc.get("enzymes", [])),
                    "path": str(path),
                }
            )
        except Exception:
            rows.append({"name": path.stem, "updated_at": "", "count": 0, "path": str(path)})
    for name, enzymes in sorted(BUILTIN_ENZYME_SETS.items()):
        rows.append({"name": name, "updated_at": "builtin", "count": len(enzymes), "path": "builtin", "builtin": True})
    return {"count": len(rows), "sets": rows}


def load_enzyme_set(name: str) -> Dict[str, Any]:
    if name in BUILTIN_ENZYME_SETS:
        return {"name": name, "updated_at": "builtin", "enzymes": list(BUILTIN_ENZYME_SETS[name]), "builtin": True}
    path = enzyme_set_path(name)
    if not path.exists():
        raise ValueError("Enzyme set not found")
    return json.loads(path.read_text(encoding="utf-8"))


def delete_enzyme_set(name: str) -> Dict[str, Any]:
    if name in BUILTIN_ENZYME_SETS:
        raise ValueError("Cannot delete built-in enzyme set")
    path = enzyme_set_path(name)
    if not path.exists():
        raise ValueError("Enzyme set not found")
    path.unlink()
    return {"deleted": True, "name": name}


def list_predefined_enzyme_sets() -> Dict[str, Any]:
    rows = [{"name": name, "enzymes": enzymes, "count": len(enzymes)} for name, enzymes in sorted(BUILTIN_ENZYME_SETS.items())]
    return {"count": len(rows), "sets": rows}


def resolve_enzymes(payload: Dict[str, Any]) -> List[str]:
    enzymes = payload.get("enzymes", [])
    if isinstance(enzymes, str):
        enzymes = [item.strip() for item in enzymes.split(",") if item.strip()]
    use_set = str(payload.get("enzyme_set", "")).strip()
    if use_set:
        doc = load_enzyme_set(use_set)
        enzymes = list(doc.get("enzymes", []))
    return [str(enzyme).strip() for enzyme in enzymes if str(enzyme).strip()]


def annotation_db_path(name: str) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid annotation db name")
    ANNOT_DB_DIR.mkdir(parents=True, exist_ok=True)
    return ANNOT_DB_DIR / f"{safe}.json"


def save_annotation_db(name: str, signatures: List[Dict[str, Any]]) -> Dict[str, Any]:
    path = annotation_db_path(name)
    cleaned = []
    for signature in signatures:
        if not isinstance(signature, dict):
            continue
        motif = sanitize_sequence(str(signature.get("motif", "")))
        if not motif:
            continue
        cleaned.append({"label": str(signature.get("label", motif)), "type": str(signature.get("type", "misc_feature")), "motif": motif})
    doc = {"name": name, "updated_at": datetime.now(timezone.utc).isoformat(), "signatures": cleaned}
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"saved": True, "name": name, "count": len(cleaned), "path": str(path)}


def list_annotation_dbs() -> Dict[str, Any]:
    ANNOT_DB_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(ANNOT_DB_DIR.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "name": doc.get("name", path.stem),
                    "updated_at": doc.get("updated_at", ""),
                    "count": len(doc.get("signatures", [])),
                    "path": str(path),
                }
            )
        except Exception:
            rows.append({"name": path.stem, "updated_at": "", "count": 0, "path": str(path)})
    return {"count": len(rows), "databases": rows}


def load_annotation_db(name: str) -> Dict[str, Any]:
    path = annotation_db_path(name)
    if not path.exists():
        raise ValueError("Annotation DB not found")
    return json.loads(path.read_text(encoding="utf-8"))


def annotate_with_db(record: SequenceRecord, db_name: str) -> Dict[str, Any]:
    doc = load_annotation_db(db_name)
    signatures = doc.get("signatures", [])
    rows = []
    circular = record.topology == "circular"
    for signature in signatures:
        motif = sanitize_sequence(str(signature.get("motif", "")))
        if not motif:
            continue
        for pos in find_all_occurrences(record.sequence, motif, circular=circular):
            start = pos + 1
            end = pos + len(motif)
            if end > record.length and circular:
                end -= record.length
            rows.append(
                {
                    "label": str(signature.get("label", motif)),
                    "type": str(signature.get("type", "misc_feature")),
                    "motif": motif,
                    "start_1based": start,
                    "end_1based": end,
                }
            )
    rows.sort(key=lambda row: row["start_1based"])
    return {"db_name": db_name, "count": len(rows), "annotations": rows}


def gel_simulate(fragment_sizes: List[int]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not fragment_sizes:
        return rows
    cleaned = sorted([max(1, int(size)) for size in fragment_sizes], reverse=True)
    if len(cleaned) == 1:
        return [{"size_bp": cleaned[0], "relative_migration": 0.5}]
    logs = [math.log10(size) for size in cleaned]
    lo = min(logs)
    hi = max(logs)
    span = max(1e-6, hi - lo)
    for size, log_value in zip(cleaned, logs):
        norm = (log_value - lo) / span
        distance = 0.95 - 0.85 * norm
        rows.append({"size_bp": size, "relative_migration": round(distance, 3)})
    return rows


def gel_simulate_lanes(sample_sizes: List[int], marker_set: str = "1kb_plus") -> Dict[str, Any]:
    marker_key = marker_set if marker_set in GEL_MARKER_SETS else "1kb_plus"
    marker_sizes = GEL_MARKER_SETS[marker_key]
    return {
        "marker_set": marker_key,
        "marker_bands": gel_simulate(marker_sizes),
        "sample_bands": gel_simulate(sample_sizes),
        "available_marker_sets": sorted(GEL_MARKER_SETS.keys()),
    }


def pcr_gel_lanes(
    record: SequenceRecord,
    primer_pairs: List[Dict[str, Any]],
    marker_set: str = "1kb_plus",
) -> Dict[str, Any]:
    lanes = []
    sample_sizes: List[int] = []
    for lane, pair in enumerate(primer_pairs, start=1):
        forward = str(pair.get("forward", "")).strip()
        reverse = str(pair.get("reverse", "")).strip()
        if not forward or not reverse:
            lanes.append({"lane": lane, "error": "forward/reverse required"})
            continue
        pcr = simulate_pcr(record, forward_primer=forward, reverse_primer=reverse)
        products = pcr.get("products", [])
        sizes = [int(product.get("size_bp", 0)) for product in products if int(product.get("size_bp", 0)) > 0]
        sample_sizes.extend(sizes)
        lanes.append(
            {
                "lane": lane,
                "forward": forward,
                "reverse": reverse,
                "product_count": len(products),
                "product_sizes_bp": sizes,
                "bands": gel_simulate(sizes),
            }
        )
    out = gel_simulate_lanes(sample_sizes=sample_sizes, marker_set=marker_set)
    out["lanes"] = lanes
    return out


def handle_biology_endpoint(path: str, payload: Dict[str, Any], get_record: RecordGetter) -> Dict[str, Any] | None:
    if path == "/api/digest":
        return simulate_digest(get_record(), resolve_enzymes(payload))
    if path == "/api/digest-advanced":
        methylated = payload.get("methylated_motifs", [])
        if isinstance(methylated, str):
            methylated = [item.strip() for item in methylated.split(",") if item.strip()]
        return digest_with_methylation(get_record(), resolve_enzymes(payload), methylated)
    if path == "/api/star-activity-scan":
        return star_activity_scan(
            get_record(),
            enzymes=resolve_enzymes(payload),
            star_activity_level=float(payload.get("star_activity_level", 0.0)),
            include_star_cuts=bool(payload.get("include_star_cuts", False)),
        )
    if path == "/api/primer-diagnostics":
        return primer_diagnostics(
            forward=str(payload.get("forward", "")),
            reverse=str(payload.get("reverse", "")),
            na_mM=float(payload.get("na_mM", 50.0)),
            primer_nM=float(payload.get("primer_nM", 250.0)),
        )
    if path == "/api/annotate-auto":
        return auto_annotate(get_record())
    if path == "/api/annot-db-save":
        db_name = str(payload.get("db_name", "")).strip()
        signatures = payload.get("signatures", [])
        if isinstance(signatures, str):
            signatures = json.loads(signatures)
        return save_annotation_db(db_name, signatures)
    if path == "/api/annot-db-list":
        return list_annotation_dbs()
    if path == "/api/annot-db-load":
        return load_annotation_db(str(payload.get("db_name", "")).strip())
    if path == "/api/annot-db-apply":
        return annotate_with_db(get_record(), str(payload.get("db_name", "")).strip())
    if path == "/api/features-list":
        record = get_record()
        return {"count": len(record.features), "features": features_to_dict(record.features)}
    if path == "/api/features-add":
        record = get_record()
        qualifiers = payload.get("qualifiers", {})
        if isinstance(qualifiers, dict):
            q = {str(k): str(v) for k, v in qualifiers.items()}
        else:
            q = {}
        record.features.append(
            Feature(
                key=str(payload.get("key", "misc_feature")),
                location=str(payload.get("location", "")),
                qualifiers=q,
            )
        )
        return {"count": len(record.features), "features": features_to_dict(record.features)}
    if path == "/api/features-update":
        record = get_record()
        idx = int(payload.get("index", -1))
        if idx < 0 or idx >= len(record.features):
            raise ValueError("feature index out of range")
        feature = record.features[idx]
        if "key" in payload:
            feature.key = str(payload.get("key"))
        if "location" in payload:
            feature.location = str(payload.get("location"))
        if "qualifiers" in payload and isinstance(payload.get("qualifiers"), dict):
            feature.qualifiers = {str(k): str(v) for k, v in payload["qualifiers"].items()}
        return {"count": len(record.features), "features": features_to_dict(record.features)}
    if path == "/api/features-delete":
        record = get_record()
        idx = int(payload.get("index", -1))
        if idx < 0 or idx >= len(record.features):
            raise ValueError("feature index out of range")
        del record.features[idx]
        return {"count": len(record.features), "features": features_to_dict(record.features)}
    if path == "/api/enzyme-scan":
        record = get_record()
        names = resolve_enzymes(payload)
        if not names:
            names = sorted(ENZYMES.keys())
        hits = []
        for name in names:
            site, _ = ENZYMES[name]
            positions = find_all_occurrences(record.sequence, site, circular=record.topology == "circular")
            if positions:
                hits.append(
                    {
                        "enzyme": name,
                        "site": site,
                        "count": len(positions),
                        "positions_1based": [pos + 1 for pos in positions[:20]],
                    }
                )
        return {"hit_count": len(hits), "enzymes": hits}
    if path == "/api/enzyme-info":
        names = resolve_enzymes(payload)
        if not names:
            names = sorted(ENZYME_META.keys())
        rows = []
        for name in names:
            if name in ENZYME_META:
                rows.append({"enzyme": name, **ENZYME_META[name]})
        return {"count": len(rows), "enzymes": rows}
    if path == "/api/enzyme-set-save":
        enzymes = payload.get("enzymes", [])
        if isinstance(enzymes, str):
            enzymes = [item.strip() for item in enzymes.split(",") if item.strip()]
        return save_enzyme_set(str(payload.get("set_name", "")).strip(), [str(item) for item in enzymes], notes=str(payload.get("notes", "")))
    if path == "/api/enzyme-set-list":
        return list_enzyme_sets()
    if path == "/api/enzyme-set-predefined":
        return list_predefined_enzyme_sets()
    if path == "/api/enzyme-set-load":
        return load_enzyme_set(str(payload.get("set_name", "")).strip())
    if path == "/api/enzyme-set-delete":
        return delete_enzyme_set(str(payload.get("set_name", "")).strip())
    if path == "/api/gel-sim":
        sizes = payload.get("sizes", [])
        if isinstance(sizes, str):
            sizes = [int(item.strip()) for item in sizes.split(",") if item.strip()]
        marker_set = str(payload.get("marker_set", "1kb_plus")).strip() or "1kb_plus"
        return gel_simulate_lanes([int(item) for item in sizes], marker_set=marker_set)
    if path == "/api/gel-marker-sets":
        return {"marker_sets": GEL_MARKER_SETS, "count": len(GEL_MARKER_SETS)}
    if path == "/api/pcr-gel-lanes":
        pairs = payload.get("primer_pairs", [])
        if isinstance(pairs, dict):
            pairs = [pairs]
        return pcr_gel_lanes(
            get_record(),
            primer_pairs=[dict(item) for item in pairs if isinstance(item, dict)],
            marker_set=str(payload.get("marker_set", "1kb_plus")),
        )
    return None
