from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

from genomeforge_toolkit import (
    AA_TO_CODONS,
    CODON_TABLE,
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
GEL_LADDER_DIR = ROOT / "gel_ladders"
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


def _parse_size_list(value: Any) -> List[int]:
    if isinstance(value, str):
        raw_items = value.replace("\n", ",").split(",")
    elif isinstance(value, list):
        raw_items = value
    else:
        raw_items = []
    sizes: List[int] = []
    for item in raw_items:
        try:
            size = int(str(item).strip())
        except ValueError:
            continue
        if 1 <= size <= 1_000_000:
            sizes.append(size)
    return sorted(set(sizes), reverse=True)


def gel_ladder_path(name: str) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid gel ladder name")
    GEL_LADDER_DIR.mkdir(parents=True, exist_ok=True)
    return GEL_LADDER_DIR / f"{safe}.json"


def save_gel_ladder(name: str, sizes: Any, notes: str = "") -> Dict[str, Any]:
    if name in GEL_MARKER_SETS:
        raise ValueError("Custom ladder name conflicts with a built-in marker set")
    parsed = _parse_size_list(sizes)
    if not parsed:
        raise ValueError("At least one ladder size is required")
    path = gel_ladder_path(name)
    doc = {"name": name, "updated_at": datetime.now(timezone.utc).isoformat(), "sizes": parsed, "notes": notes}
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"saved": True, "name": name, "count": len(parsed), "sizes": parsed, "path": str(path)}


def load_gel_ladder(name: str) -> Dict[str, Any]:
    if name in GEL_MARKER_SETS:
        return {"name": name, "updated_at": "builtin", "sizes": list(GEL_MARKER_SETS[name]), "builtin": True}
    path = gel_ladder_path(name)
    if not path.exists():
        raise ValueError("Gel ladder not found")
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {
        "name": str(doc.get("name", name)),
        "updated_at": str(doc.get("updated_at", "")),
        "sizes": _parse_size_list(doc.get("sizes", [])),
        "notes": str(doc.get("notes", "")),
        "builtin": False,
    }


def list_gel_ladders() -> Dict[str, Any]:
    GEL_LADDER_DIR.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    for name, sizes in sorted(GEL_MARKER_SETS.items()):
        rows.append({"name": name, "updated_at": "builtin", "count": len(sizes), "sizes": list(sizes), "builtin": True})
    for path in sorted(GEL_LADDER_DIR.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            sizes = _parse_size_list(doc.get("sizes", []))
            rows.append(
                {
                    "name": str(doc.get("name", path.stem)),
                    "updated_at": str(doc.get("updated_at", "")),
                    "count": len(sizes),
                    "sizes": sizes,
                    "path": str(path),
                    "builtin": False,
                }
            )
        except Exception:
            rows.append({"name": path.stem, "updated_at": "", "count": 0, "sizes": [], "path": str(path), "builtin": False})
    return {"count": len(rows), "ladders": rows}


def delete_gel_ladder(name: str) -> Dict[str, Any]:
    if name in GEL_MARKER_SETS:
        raise ValueError("Cannot delete built-in marker set")
    path = gel_ladder_path(name)
    if not path.exists():
        raise ValueError("Gel ladder not found")
    path.unlink()
    return {"deleted": True, "name": name}


def _available_marker_set_names() -> List[str]:
    custom = []
    if GEL_LADDER_DIR.exists():
        custom = [path.stem for path in sorted(GEL_LADDER_DIR.glob("*.json"))]
    return sorted(set(GEL_MARKER_SETS.keys()) | set(custom))


def _resolve_marker_sizes(marker_set: str) -> tuple[str, List[int], bool]:
    marker_key = str(marker_set or "1kb_plus").strip() or "1kb_plus"
    if marker_key in GEL_MARKER_SETS:
        return marker_key, list(GEL_MARKER_SETS[marker_key]), False
    try:
        ladder = load_gel_ladder(marker_key)
        sizes = _parse_size_list(ladder.get("sizes", []))
        if sizes:
            return str(ladder.get("name", marker_key)), sizes, True
    except Exception:
        pass
    return "1kb_plus", list(GEL_MARKER_SETS["1kb_plus"]), False


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


def _feature_label(feature: Feature) -> str:
    qualifiers = getattr(feature, "qualifiers", {}) or {}
    for key in ("label", "gene", "product", "note"):
        if str(qualifiers.get(key, "")).strip():
            return str(qualifiers[key]).strip()
    return str(getattr(feature, "key", "feature") or "feature")


def _feature_bounds(location: str, record_length: int) -> tuple[int, int] | None:
    nums = [int(item) for item in str(location or "").replace("<", "").replace(">", "").split() if item.isdigit()]
    if len(nums) < 2:
        nums = [int(item) for item in re.findall(r"\d+", str(location or ""))]
    if len(nums) < 2:
        return None
    start = max(1, min(record_length, nums[0]))
    end = max(1, min(record_length, nums[-1]))
    if start > end:
        start, end = end, start
    return start, end


def build_text_map(record: SequenceRecord, start_1based: int = 1, end_1based: int = 0, width: int = 80, frame: int = 1) -> Dict[str, Any]:
    seq = record.sequence
    if not seq:
        raise ValueError("sequence is empty")
    n = len(seq)
    start = max(1, int(start_1based))
    end = n if int(end_1based) <= 0 else min(n, int(end_1based))
    if start > end:
        raise ValueError("Invalid text-map range")
    width = max(30, min(160, int(width)))
    frame0 = max(0, min(2, int(frame) - 1))
    lines: List[str] = [
        f"Genome Forge text map: {record.name} ({record.topology}, {n} bp)",
        f"Range {start}..{end}; width {width}; translation frame {frame0 + 1}",
        "",
    ]
    feature_rows = []
    for idx, feature in enumerate(record.features):
        bounds = _feature_bounds(str(getattr(feature, "location", "")), n)
        if not bounds:
            continue
        feature_rows.append({"index": idx, "start": bounds[0], "end": bounds[1], "label": _feature_label(feature), "key": feature.key})

    chunk_count = 0
    for chunk_start in range(start, end + 1, width):
        chunk_end = min(end, chunk_start + width - 1)
        chunk = seq[chunk_start - 1 : chunk_end]
        aa_line = [" "] * len(chunk)
        for offset in range(len(chunk)):
            global0 = chunk_start - 1 + offset
            if global0 < frame0 or (global0 - frame0) % 3 != 0 or global0 + 3 > n:
                continue
            codon = seq[global0 : global0 + 3]
            residue = CODON_TABLE.get(codon, "X")
            if offset + 1 < len(aa_line):
                aa_line[offset + 1] = residue

        lines.append(f"{chunk_start:>6}  {chunk}")
        lines.append(f"        {''.join(aa_line)}")
        overlapping = [row for row in feature_rows if row["end"] >= chunk_start and row["start"] <= chunk_end]
        for row in overlapping[:8]:
            graphic = [" "] * len(chunk)
            left = max(row["start"], chunk_start) - chunk_start
            right = min(row["end"], chunk_end) - chunk_start
            for i in range(max(0, left), min(len(graphic), right + 1)):
                graphic[i] = "="
            label = f"[{row['label']}]"
            label_pos = max(0, min(len(graphic) - len(label), left))
            for i, ch in enumerate(label):
                if label_pos + i < len(graphic):
                    graphic[label_pos + i] = ch
            lines.append(f"feat{row['index']:<3}  {''.join(graphic)}  {row['key']}")
        lines.append("")
        chunk_count += 1

    return {
        "name": record.name,
        "length": n,
        "start_1based": start,
        "end_1based": end,
        "width": width,
        "frame": frame0 + 1,
        "feature_count": len(feature_rows),
        "chunk_count": chunk_count,
        "text_map": "\n".join(lines).rstrip() + "\n",
        "features": feature_rows,
    }


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


def _enzyme_cut_positions(sequence: str, topology: str, enzyme: str) -> List[int]:
    seq = sanitize_sequence(sequence)
    if not seq or enzyme not in ENZYMES:
        return []
    site, offset = ENZYMES[enzyme]
    circular = str(topology).lower() == "circular"
    positions = []
    for pos0 in find_all_occurrences(seq, site, circular=circular):
        cut = ((pos0 + offset) % len(seq)) + 1 if circular else pos0 + offset + 1
        positions.append(cut)
    return sorted(positions)


def restriction_site_compare(
    record_a: SequenceRecord,
    sequence_b: str,
    enzymes: List[str],
    topology_b: str = "linear",
    min_delta: int = 1,
) -> Dict[str, Any]:
    seq_b = sanitize_sequence(sequence_b)
    if not seq_b:
        raise ValueError("sequence_b is required")
    names = enzymes or sorted(ENZYMES.keys())
    rows: List[Dict[str, Any]] = []
    for enzyme in names:
        if enzyme not in ENZYMES:
            continue
        site, _ = ENZYMES[enzyme]
        cuts_a = _enzyme_cut_positions(record_a.sequence, record_a.topology, enzyme)
        cuts_b = _enzyme_cut_positions(seq_b, topology_b, enzyme)
        delta = len(cuts_a) - len(cuts_b)
        if delta == 0:
            category = "same"
        elif len(cuts_b) == 0:
            category = "unique_to_a"
        elif len(cuts_a) == 0:
            category = "unique_to_b"
        elif delta > 0:
            category = "higher_in_a"
        else:
            category = "higher_in_b"
        rows.append(
            {
                "enzyme": enzyme,
                "site": site,
                "count_a": len(cuts_a),
                "count_b": len(cuts_b),
                "delta_a_minus_b": delta,
                "abs_delta": abs(delta),
                "category": category,
                "positions_a_1based": cuts_a[:50],
                "positions_b_1based": cuts_b[:50],
                "diagnostic": abs(delta) >= max(1, int(min_delta)),
            }
        )
    rows.sort(key=lambda row: (row["diagnostic"], row["abs_delta"], row["enzyme"]), reverse=True)
    diagnostic = [row for row in rows if row["diagnostic"]]
    return {
        "sequence_a_name": record_a.name,
        "sequence_a_length": record_a.length,
        "sequence_b_length": len(seq_b),
        "enzyme_count": len(rows),
        "diagnostic_count": len(diagnostic),
        "diagnostic_candidates": diagnostic,
        "comparisons": rows,
    }


def silent_restriction_sites(
    record: SequenceRecord,
    enzymes: List[str],
    frame: int = 1,
    max_candidates: int = 100,
) -> Dict[str, Any]:
    seq = record.sequence
    if not seq:
        raise ValueError("sequence is empty")
    names = enzymes or sorted(ENZYMES.keys())
    frame0 = max(0, min(2, int(frame) - 1))
    existing = {
        enzyme: set(find_all_occurrences(seq, ENZYMES[enzyme][0], circular=False))
        for enzyme in names
        if enzyme in ENZYMES
    }
    candidates: List[Dict[str, Any]] = []
    seen = set()
    for codon_start0 in range(frame0, len(seq) - 2, 3):
        codon = seq[codon_start0 : codon_start0 + 3]
        aa = CODON_TABLE.get(codon)
        if not aa or aa == "*":
            continue
        for new_codon in AA_TO_CODONS.get(aa, []):
            if new_codon == codon:
                continue
            mutated = seq[:codon_start0] + new_codon + seq[codon_start0 + 3 :]
            mutation_positions = [
                {
                    "position_1based": codon_start0 + i + 1,
                    "from": codon[i],
                    "to": new_codon[i],
                }
                for i in range(3)
                if codon[i] != new_codon[i]
            ]
            for enzyme in names:
                if enzyme not in ENZYMES:
                    continue
                site, offset = ENZYMES[enzyme]
                new_hits = set(find_all_occurrences(mutated, site, circular=False)) - existing.get(enzyme, set())
                for site_start0 in sorted(new_hits):
                    site_end0 = site_start0 + len(site) - 1
                    overlaps_codon = site_start0 <= codon_start0 + 2 and site_end0 >= codon_start0
                    if not overlaps_codon:
                        continue
                    key = (enzyme, codon_start0, new_codon, site_start0)
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append(
                        {
                            "enzyme": enzyme,
                            "site": site,
                            "site_start_1based": site_start0 + 1,
                            "site_end_1based": site_end0 + 1,
                            "cut_position_1based": site_start0 + offset + 1,
                            "protein_position_1based": ((codon_start0 - frame0) // 3) + 1,
                            "aa": aa,
                            "original_codon": codon,
                            "silent_codon": new_codon,
                            "mutations": mutation_positions,
                            "introduced_site": mutated[site_start0 : site_start0 + len(site)],
                        }
                    )
                    if len(candidates) >= int(max_candidates):
                        return {
                            "record_name": record.name,
                            "frame": frame0 + 1,
                            "enzyme_count": len(names),
                            "candidate_count": len(candidates),
                            "candidates": candidates,
                            "truncated": True,
                        }
    candidates.sort(key=lambda row: (row["site_start_1based"], row["enzyme"], row["protein_position_1based"]))
    return {
        "record_name": record.name,
        "frame": frame0 + 1,
        "enzyme_count": len(names),
        "candidate_count": len(candidates),
        "candidates": candidates[: max(1, int(max_candidates))],
        "truncated": len(candidates) > int(max_candidates),
    }


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
    marker_key, marker_sizes, custom_marker = _resolve_marker_sizes(marker_set)
    return {
        "marker_set": marker_key,
        "custom_marker": custom_marker,
        "marker_bands": gel_simulate(marker_sizes),
        "sample_bands": gel_simulate(sample_sizes),
        "available_marker_sets": _available_marker_set_names(),
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
    if path == "/api/text-map":
        return build_text_map(
            get_record(),
            start_1based=int(payload.get("start", 1)),
            end_1based=int(payload.get("end", 0)),
            width=int(payload.get("width", 80)),
            frame=int(payload.get("frame", 1)),
        )
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
    if path == "/api/digest-gel":
        digest = simulate_digest(get_record(), resolve_enzymes(payload))
        gel = gel_simulate_lanes(
            [int(size) for size in digest.get("fragments_bp", [])],
            marker_set=str(payload.get("marker_set", "1kb_plus")),
        )
        return {"digest": digest, **gel}
    if path == "/api/restriction-compare":
        return restriction_site_compare(
            get_record(),
            sequence_b=str(payload.get("sequence_b", payload.get("compare_sequence", ""))),
            enzymes=resolve_enzymes(payload),
            topology_b=str(payload.get("topology_b", "linear")),
            min_delta=int(payload.get("min_delta", 1)),
        )
    if path == "/api/silent-restriction-sites":
        return silent_restriction_sites(
            get_record(),
            enzymes=resolve_enzymes(payload),
            frame=int(payload.get("frame", 1)),
            max_candidates=int(payload.get("max_candidates", 100)),
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
        marker_set = str(payload.get("marker_set", "1kb_plus")).strip() or "1kb_plus"
        return gel_simulate_lanes(_parse_size_list(sizes), marker_set=marker_set)
    if path == "/api/gel-marker-sets":
        return {"marker_sets": GEL_MARKER_SETS, "available_marker_sets": _available_marker_set_names(), "count": len(GEL_MARKER_SETS)}
    if path == "/api/gel-ladder-save":
        return save_gel_ladder(
            str(payload.get("ladder_name", payload.get("name", ""))).strip(),
            payload.get("sizes", []),
            notes=str(payload.get("notes", "")),
        )
    if path == "/api/gel-ladder-list":
        return list_gel_ladders()
    if path == "/api/gel-ladder-load":
        return load_gel_ladder(str(payload.get("ladder_name", payload.get("name", ""))).strip())
    if path == "/api/gel-ladder-delete":
        return delete_gel_ladder(str(payload.get("ladder_name", payload.get("name", ""))).strip())
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
