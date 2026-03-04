#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import math
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid
from typing import Any, Dict, List, Tuple

from canonical_schema import (
    canonical_to_payload,
    canonical_to_record,
    infer_source_format,
    record_to_canonical,
)
from bio.trace_tools import align_trace_to_reference, edit_trace_base, trace_consensus, trace_summary
from bio.crispr_design import crispr_offtarget_scan, design_grna_candidates, design_hdr_template
from bio.project_diff import diff_projects
from bio.primer_specificity import primer_specificity_report, rank_primer_pairs
from collab.review import approve_review, submit_review
from collab.store import (
    append_audit_event,
    create_workspace,
    get_audit_log,
    get_project_permissions,
    role_for_user,
    set_project_permissions,
)
from compat.ab1_format import parse_ab1_bytes, synthetic_trace_from_sequence
from compat.dna_format import export_dna_container, import_dna_container
from genomeforge_toolkit import (
    CODON_TABLE,
    ENZYMES,
    Feature,
    SequenceRecord,
    build_svg_map,
    design_primer_pair,
    find_all_occurrences,
    optimize_coding_sequence,
    parse_fasta,
    parse_genbank,
    primer_quality,
    sanitize_sequence,
    seq_tm_nn,
    simulate_digest,
    simulate_pcr,
    to_fasta,
    to_embl,
    to_genbank,
)

ROOT = Path(__file__).resolve().parent
INDEX_PATH = ROOT / "webui" / "index.html"
PROJECTS_DIR = ROOT / "projects"
ANNOT_DB_DIR = ROOT / "annotation_db"
ENZYME_SET_DIR = ROOT / "enzyme_sets"
COLLECTIONS_DIR = ROOT / "collections"
SHARES_DIR = ROOT / "shares"
COLLAB_ROOT = ROOT / "collab_data"
TRACE_CACHE: Dict[str, Dict[str, Any]] = {}


AA_TO_CODONS: Dict[str, List[str]] = {}
for codon, aa in CODON_TABLE.items():
    AA_TO_CODONS.setdefault(aa, []).append(codon)

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

# Simplified sticky-end model for common enzymes.
ENZYME_STICKY_ENDS: Dict[str, Dict[str, str]] = {
    "EcoRI": {"overhang": "AATT", "polarity": "5prime"},
    "BamHI": {"overhang": "GATC", "polarity": "5prime"},
    "HindIII": {"overhang": "AGCT", "polarity": "5prime"},
    "XhoI": {"overhang": "TCGA", "polarity": "5prime"},
    "XbaI": {"overhang": "CTAG", "polarity": "5prime"},
    "SpeI": {"overhang": "CTAG", "polarity": "5prime"},
    "NheI": {"overhang": "CTAG", "polarity": "5prime"},
    "KpnI": {"overhang": "GTAC", "polarity": "3prime"},
    "PstI": {"overhang": "TGCA", "polarity": "3prime"},
    "NotI": {"overhang": "CG", "polarity": "5prime"},
}


def _slice_circular(seq: str, start: int, length: int) -> str:
    n = len(seq)
    if n == 0 or length <= 0:
        return ""
    out = []
    for i in range(length):
        out.append(seq[(start + i) % n])
    return "".join(out)

RC = str.maketrans("ACGTN", "TGCAN")

ANNOTATION_PATTERNS: List[Dict[str, str]] = [
    {"label": "Bacterial -10 box", "type": "promoter", "motif": "TATAAT"},
    {"label": "Bacterial -35 box", "type": "promoter", "motif": "TTGACA"},
    {"label": "Shine-Dalgarno", "type": "rbs", "motif": "AGGAGG"},
    {"label": "FLAG tag", "type": "tag", "motif": "GACTACAAGGACGACGATGACAAG"},
    {"label": "His6 tag", "type": "tag", "motif": "CATCACCATCACCATCAC"},
    {"label": "T7 promoter", "type": "promoter", "motif": "TAATACGACTCACTATAGGG"},
]


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
        for f in payload["features"]:
            if not isinstance(f, dict):
                continue
            feats.append(
                Feature(
                    key=str(f.get("key", "misc_feature")),
                    location=str(f.get("location", "")),
                    qualifiers={k: str(v) for k, v in dict(f.get("qualifiers", {})).items()},
                )
            )
        record.features = feats
    return record


def _decode_b64_field(value: str, label: str) -> bytes:
    if not value:
        raise ValueError(f"{label} is required")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"{label} must be valid base64: {e}") from e


def _encode_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _cache_trace(trace_record: Dict[str, Any]) -> Dict[str, Any]:
    tid = str(trace_record.get("trace_id", "")).strip()
    if not tid:
        tid = "trace_" + uuid.uuid4().hex[:12]
        trace_record["trace_id"] = tid
    TRACE_CACHE[tid] = trace_record
    # Keep cache bounded for local runtime.
    if len(TRACE_CACHE) > 32:
        for old in list(TRACE_CACHE.keys())[: len(TRACE_CACHE) - 32]:
            TRACE_CACHE.pop(old, None)
    return trace_record


def _resolve_trace(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload.get("trace_record"), dict):
        return dict(payload["trace_record"])
    trace_id = str(payload.get("trace_id", "")).strip()
    if trace_id and trace_id in TRACE_CACHE:
        return dict(TRACE_CACHE[trace_id])
    raise ValueError("trace_record or known trace_id is required")


def parse_plain_sequence(seq: str) -> str:
    return sanitize_sequence(seq)


def revcomp(seq: str) -> str:
    return parse_plain_sequence(seq).translate(RC)[::-1]


def is_complementary(a: str, b: str) -> bool:
    return parse_plain_sequence(a) == revcomp(parse_plain_sequence(b))


def digest_with_methylation(
    record: SequenceRecord,
    enzymes: List[str],
    methylated_motifs: List[str],
) -> Dict[str, Any]:
    raw = simulate_digest(record, enzymes)
    methyl = [parse_plain_sequence(x) for x in methylated_motifs if str(x).strip()]
    blocked_positions = set()
    blocked_details: List[Dict[str, Any]] = []
    for enz in enzymes:
        site = ENZYME_META.get(enz, {}).get("site")
        if site and site in methyl:
            positions = find_all_occurrences(record.sequence, site, circular=record.topology == "circular")
            offset = ENZYME_META.get(enz, {}).get("cut_offset", 0)
            for p in positions:
                cut_1based = ((p + offset) % record.length) + 1 if record.topology == "circular" else (p + offset + 1)
                blocked_positions.add(cut_1based)
                blocked_details.append({"enzyme": enz, "site": site, "position_1based": cut_1based})

    cuts = [c for c in raw["cuts"] if c["position_1based"] not in blocked_positions]
    unique_cut_positions = sorted({c["position_1based"] for c in cuts})
    if not unique_cut_positions:
        fragments = [record.length]
    elif record.topology == "circular":
        if len(unique_cut_positions) == 1:
            fragments = [record.length]
        else:
            z = [p - 1 for p in unique_cut_positions]
            fragments = [(z[(i + 1) % len(z)] - z[i]) % record.length for i in range(len(z))]
    else:
        bounds = [1] + unique_cut_positions + [record.length + 1]
        fragments = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]

    return {
        "topology": record.topology,
        "methylated_motifs": methyl,
        "blocked_cuts": blocked_details,
        "cuts": cuts,
        "unique_cut_positions_1based": unique_cut_positions,
        "fragments_bp": sorted([f for f in fragments if f > 0], reverse=True),
    }


def _hamming(a: str, b: str) -> int:
    if len(a) != len(b):
        return max(len(a), len(b))
    return sum(1 for x, y in zip(a, b) if x != y)


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
    for enz in enzymes:
        if enz not in ENZYMES:
            continue
        site, offset = ENZYMES[enz]
        m = len(site)
        scan_seq = seq + (seq[: m - 1] if circular else "")
        limit = n if circular else n - m + 1
        for i in range(max(0, limit)):
            motif = scan_seq[i : i + m]
            if len(motif) != m:
                continue
            mm = _hamming(motif, site)
            if mm == 0:
                continue
            if mm <= max_mismatch:
                cut = ((i + offset) % n) + 1 if circular else (i + offset + 1)
                star_hits.append(
                    {
                        "enzyme": enz,
                        "site": site,
                        "matched": motif,
                        "mismatches": mm,
                        "site_start_1based": i + 1,
                        "cut_position_1based": cut,
                    }
                )
                star_cut_points.append(cut)

    star_hits.sort(key=lambda x: (x["mismatches"], x["cut_position_1based"]))
    out = {
        "star_activity_level": level,
        "max_mismatch": max_mismatch,
        "exact_digest": exact,
        "star_hits": star_hits,
        "star_hit_count": len(star_hits),
    }
    if include_star_cuts:
        cuts = list(exact["cuts"]) + [{"enzyme": "STAR", "position_1based": p} for p in star_cut_points]
        uniq = sorted({c["position_1based"] for c in cuts})
        if not uniq:
            frags = [record.length]
        elif record.topology == "circular":
            if len(uniq) == 1:
                frags = [record.length]
            else:
                z = [p - 1 for p in uniq]
                frags = [(z[(i + 1) % len(z)] - z[i]) % record.length for i in range(len(z))]
        else:
            bounds = [1] + uniq + [record.length + 1]
            frags = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]
        out["digest_with_star"] = {
            "cuts": sorted(cuts, key=lambda x: x["position_1based"]),
            "unique_cut_positions_1based": uniq,
            "fragments_bp": sorted([f for f in frags if f > 0], reverse=True),
        }
    return out


def reverse_translate_protein(protein: str, host: str = "ecoli") -> str:
    # Reuse host preference through optimize pathway by creating pseudo amino sequence mapping.
    prefs = {
        "ecoli": {
            "A": "GCG", "R": "CGT", "N": "AAC", "D": "GAT", "C": "TGC",
            "Q": "CAG", "E": "GAA", "G": "GGC", "H": "CAC", "I": "ATC",
            "L": "CTG", "K": "AAA", "M": "ATG", "F": "TTC", "P": "CCG",
            "S": "TCG", "T": "ACC", "W": "TGG", "Y": "TAC", "V": "GTG", "*": "TAA",
        },
        "yeast": {
            "A": "GCT", "R": "AGA", "N": "AAT", "D": "GAT", "C": "TGT",
            "Q": "CAA", "E": "GAA", "G": "GGT", "H": "CAT", "I": "ATT",
            "L": "TTG", "K": "AAA", "M": "ATG", "F": "TTT", "P": "CCA",
            "S": "TCT", "T": "ACT", "W": "TGG", "Y": "TAT", "V": "GTT", "*": "TAA",
        },
    }
    host = host.lower()
    pref = prefs.get(host, prefs["ecoli"])
    aa = protein.strip().upper()
    if not aa:
        raise ValueError("protein is required")
    codons: List[str] = []
    for residue in aa:
        if residue not in pref and residue not in AA_TO_CODONS:
            raise ValueError(f"Unsupported amino acid: {residue}")
        codons.append(pref.get(residue, AA_TO_CODONS[residue][0]))
    return "".join(codons)


def needleman_wunsch(
    seq_a: str,
    seq_b: str,
    match: int = 1,
    mismatch: int = -1,
    gap: int = -2,
) -> Dict[str, Any]:
    a = parse_plain_sequence(seq_a)
    b = parse_plain_sequence(seq_b)
    m, n = len(a), len(b)
    score = [[0] * (n + 1) for _ in range(m + 1)]
    trace = [[0] * (n + 1) for _ in range(m + 1)]  # 1 diag, 2 up, 3 left
    for i in range(1, m + 1):
        score[i][0] = i * gap
        trace[i][0] = 2
    for j in range(1, n + 1):
        score[0][j] = j * gap
        trace[0][j] = 3
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s_diag = score[i - 1][j - 1] + (match if a[i - 1] == b[j - 1] else mismatch)
            s_up = score[i - 1][j] + gap
            s_left = score[i][j - 1] + gap
            best = max(s_diag, s_up, s_left)
            score[i][j] = best
            trace[i][j] = 1 if best == s_diag else (2 if best == s_up else 3)

    i, j = m, n
    aa: List[str] = []
    bb: List[str] = []
    while i > 0 or j > 0:
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
        else:
            aa.append("-")
            bb.append(b[j - 1])
            j -= 1
    aln_a = "".join(reversed(aa))
    aln_b = "".join(reversed(bb))
    ident = sum(1 for x, y in zip(aln_a, aln_b) if x == y and x != "-")
    aln_len = max(len(aln_a), 1)
    return {
        "score": score[m][n],
        "identity_pct": round(ident / aln_len * 100.0, 2),
        "aligned_a": aln_a,
        "aligned_b": aln_b,
    }


def needleman_wunsch_protein(
    seq_a: str,
    seq_b: str,
    match: int = 2,
    mismatch: int = -1,
    gap: int = -3,
) -> Dict[str, Any]:
    a = "".join(ch for ch in str(seq_a).upper() if ch.isalpha() or ch in {"*", "-"})
    b = "".join(ch for ch in str(seq_b).upper() if ch.isalpha() or ch in {"*", "-"})
    if not a or not b:
        raise ValueError("Protein sequences are required")
    m, n = len(a), len(b)
    score = [[0] * (n + 1) for _ in range(m + 1)]
    trace = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        score[i][0] = i * gap
        trace[i][0] = 2
    for j in range(1, n + 1):
        score[0][j] = j * gap
        trace[0][j] = 3
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s_diag = score[i - 1][j - 1] + (match if a[i - 1] == b[j - 1] else mismatch)
            s_up = score[i - 1][j] + gap
            s_left = score[i][j - 1] + gap
            best = max(s_diag, s_up, s_left)
            score[i][j] = best
            trace[i][j] = 1 if best == s_diag else (2 if best == s_up else 3)
    i, j = m, n
    aa: List[str] = []
    bb: List[str] = []
    while i > 0 or j > 0:
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
        else:
            aa.append("-")
            bb.append(b[j - 1])
            j -= 1
    aln_a = "".join(reversed(aa))
    aln_b = "".join(reversed(bb))
    ident = sum(1 for x, y in zip(aln_a, aln_b) if x == y and x != "-")
    return {
        "mode": "protein",
        "score": score[m][n],
        "identity_pct": round(ident / max(1, len(aln_a)) * 100.0, 2),
        "aligned_a": aln_a,
        "aligned_b": aln_b,
    }


def anneal_oligos(forward: str, reverse: str, min_overlap: int = 10) -> Dict[str, Any]:
    f = parse_plain_sequence(forward)
    r = parse_plain_sequence(reverse)
    r_rc = r.translate(str.maketrans("ACGTN", "TGCAN"))[::-1]
    best = 0
    best_pos = -1
    max_k = min(len(f), len(r_rc))
    for k in range(max_k, min_overlap - 1, -1):
        if f[-k:] == r_rc[:k]:
            best = k
            best_pos = len(f) - k
            break
    assembled = f + (r_rc[best:] if best > 0 else "")
    return {
        "forward_len": len(f),
        "reverse_len": len(r),
        "reverse_rc": r_rc,
        "overlap_bp": best,
        "overlap_start_in_forward_1based": best_pos + 1 if best_pos >= 0 else None,
        "assembled_sequence": assembled if best > 0 else None,
    }


def gibson_assemble(fragments: List[str], min_overlap: int = 20, circular: bool = False) -> Dict[str, Any]:
    if len(fragments) < 2:
        raise ValueError("Need at least two fragments")
    frags = [parse_plain_sequence(x) for x in fragments]
    overlaps: List[Dict[str, Any]] = []
    assembled = frags[0]
    for i in range(1, len(frags)):
        prev = assembled
        nxt = frags[i]
        max_k = min(len(prev), len(nxt))
        best = 0
        for k in range(max_k, min_overlap - 1, -1):
            if prev[-k:] == nxt[:k]:
                best = k
                break
        if best < min_overlap:
            raise ValueError(f"Insufficient overlap between fragment {i} and {i+1}")
        overlaps.append({"left_fragment": i, "right_fragment": i + 1, "overlap_bp": best, "sequence": nxt[:best]})
        assembled = prev + nxt[best:]

    circular_overlap = 0
    if circular:
        max_k = min(len(assembled), len(frags[0]))
        for k in range(max_k, min_overlap - 1, -1):
            if assembled[-k:] == frags[0][:k]:
                circular_overlap = k
                assembled = assembled[:-k]
                break
        if circular_overlap < min_overlap:
            raise ValueError("Insufficient closing overlap for circular assembly")

    return {
        "fragment_count": len(frags),
        "overlaps": overlaps,
        "circular_overlap_bp": circular_overlap,
        "assembled_length": len(assembled),
        "assembled_sequence": assembled,
        "topology": "circular" if circular else "linear",
    }


def golden_gate_assemble(parts: List[Dict[str, Any]], circular: bool = True, enforce_complement: bool = True) -> Dict[str, Any]:
    if len(parts) < 2:
        raise ValueError("Need at least two parts")
    norm = []
    for i, p in enumerate(parts, start=1):
        seq = parse_plain_sequence(str(p.get("sequence", "")))
        left = parse_plain_sequence(str(p.get("left_overhang", "")))
        right = parse_plain_sequence(str(p.get("right_overhang", "")))
        if len(left) != 4 or len(right) != 4:
            raise ValueError(f"Part {i} must have 4bp left_overhang and right_overhang")
        norm.append({"sequence": seq, "left": left, "right": right})

    joins = []
    assembled = norm[0]["sequence"]
    for i in range(len(norm) - 1):
        a = norm[i]
        b = norm[i + 1]
        ok = is_complementary(a["right"], b["left"]) if enforce_complement else (a["right"] == b["left"])
        if not ok:
            raise ValueError(f"Overhang mismatch between part {i+1} and part {i+2}")
        joins.append({"left_part": i + 1, "right_part": i + 2, "left_overhang": a["right"], "right_overhang": b["left"]})
        assembled += b["sequence"]

    closing_ok = None
    if circular:
        a = norm[-1]["right"]
        b = norm[0]["left"]
        closing_ok = is_complementary(a, b) if enforce_complement else (a == b)
        if not closing_ok:
            raise ValueError("Closing overhang mismatch for circular Golden Gate assembly")

    return {
        "part_count": len(norm),
        "joins": joins,
        "closing_join_ok": closing_ok,
        "assembled_length": len(assembled),
        "assembled_sequence": assembled,
        "topology": "circular" if circular else "linear",
    }


def gateway_cloning(entry_clone: str, destination_vector: str, attl: str = "ACAAGTTTGTACAAAAAAGCAGGCT", attr: str = "ACCACTTTGTACAAGAAAGCTGGGT") -> Dict[str, Any]:
    e = parse_plain_sequence(entry_clone)
    d = parse_plain_sequence(destination_vector)
    li = e.find(attl)
    ri = e.find(attr)
    if li < 0 or ri < 0 or ri <= li:
        raise ValueError("Entry clone missing valid attL/attR sites")
    insert = e[li + len(attl) : ri]
    # Destination placeholder region between ccdB-like markers (simple proxy).
    marker_left = "CCDB"
    marker_right = "CCDB"
    dl = d.find("GGGCCC")
    dr = d.find("CCCGGG")
    if dl >= 0 and dr > dl:
        product = d[: dl + 6] + insert + d[dr:]
    else:
        product = d + insert
    return {"insert_length": len(insert), "product_length": len(product), "product_sequence": product}


def topo_cloning(vector: str, insert: str, mode: str = "TA") -> Dict[str, Any]:
    v = parse_plain_sequence(vector)
    ins = parse_plain_sequence(insert)
    mode = mode.upper()
    if mode == "TA":
        if not ins.endswith("A"):
            raise ValueError("TA mode expects insert ending with A-overhang")
    elif mode == "BLUNT":
        pass
    else:
        raise ValueError("Unsupported TOPO mode (use TA or BLUNT)")
    product = v + ins
    return {"mode": mode, "product_length": len(product), "product_sequence": product}


def ta_gc_cloning(vector: str, insert: str, mode: str = "TA") -> Dict[str, Any]:
    v = parse_plain_sequence(vector)
    ins = parse_plain_sequence(insert)
    mode = mode.upper()
    if mode == "TA":
        if not (ins.endswith("A") or ins.startswith("T")):
            raise ValueError("TA cloning expects A/T-compatible overhangs")
    elif mode == "GC":
        if not (ins.endswith("G") or ins.startswith("C")):
            raise ValueError("GC cloning expects G/C-compatible overhangs")
    else:
        raise ValueError("Unsupported mode (use TA or GC)")
    product = v + ins
    return {"mode": mode, "product_length": len(product), "product_sequence": product}


def primer_diagnostics(
    forward: str,
    reverse: str,
    na_mM: float = 50.0,
    primer_nM: float = 250.0,
) -> Dict[str, Any]:
    from genomeforge_toolkit import end_complement_run, max_complement_run, hairpin_risk

    f = sanitize_sequence(forward)
    r = sanitize_sequence(reverse)
    fq = primer_quality(f)
    rq = primer_quality(r)
    fq["tm_nn"] = seq_tm_nn(f, na_mM=na_mM, primer_nM=primer_nM)
    rq["tm_nn"] = seq_tm_nn(r, na_mM=na_mM, primer_nM=primer_nM)
    hetero = max_complement_run(f, r)
    hetero_end = end_complement_run(f, r)
    risk_flags = []
    if hetero_end >= 5:
        risk_flags.append("high_3prime_heterodimer")
    if fq["hairpin_stem"] >= 6 or rq["hairpin_stem"] >= 6:
        risk_flags.append("strong_hairpin")
    if abs(fq["tm_nn"] - rq["tm_nn"]) > 5:
        risk_flags.append("tm_imbalance")
    return {
        "conditions": {"na_mM": na_mM, "primer_nM": primer_nM},
        "forward": fq,
        "reverse": rq,
        "pair": {
            "heterodimer_run": hetero,
            "heterodimer_3prime_run": hetero_end,
            "tm_delta": round(abs(float(fq["tm_nn"]) - float(rq["tm_nn"])), 2),
            "predicted_risk_flags": risk_flags,
        },
    }


def cloning_compatibility_check(
    mode: str,
    vector: str = "",
    insert: str = "",
    enzymes: List[str] | None = None,
    left_overhang: str = "",
    right_overhang: str = "",
    min_overlap: int = 15,
) -> Dict[str, Any]:
    mode = mode.lower().strip()
    messages: List[str] = []
    ok = True

    if mode == "restriction":
        if not enzymes:
            return {"mode": mode, "ok": False, "messages": ["No enzymes provided"], "checks": {}}
        v = sanitize_sequence(vector)
        i = sanitize_sequence(insert)
        checks = {}
        for e in enzymes:
            if e not in ENZYMES:
                ok = False
                messages.append(f"Unknown enzyme {e}")
                continue
            site = ENZYMES[e][0]
            vc = len(find_all_occurrences(v, site, circular=True))
            ic = len(find_all_occurrences(i, site, circular=False))
            checks[e] = {"site": site, "vector_sites": vc, "insert_sites": ic}
            if vc == 0:
                ok = False
                messages.append(f"{e}: no site in vector")
            if ic == 0:
                ok = False
                messages.append(f"{e}: no site in insert")
        if ok:
            messages.append("Restriction compatibility check passed")
        return {"mode": mode, "ok": ok, "messages": messages, "checks": checks}

    if mode in {"golden_gate", "golden-gate"}:
        lo = sanitize_sequence(left_overhang) if left_overhang else ""
        ro = sanitize_sequence(right_overhang) if right_overhang else ""
        if len(lo) != 4 or len(ro) != 4:
            return {"mode": mode, "ok": False, "messages": ["Provide 4bp left/right overhangs"], "checks": {}}
        comp = is_complementary(lo, ro)
        if not comp:
            ok = False
            messages.append("Overhangs are not complementary")
        else:
            messages.append("Overhangs are complementary")
        return {"mode": mode, "ok": ok, "messages": messages, "checks": {"left_overhang": lo, "right_overhang": ro}}

    if mode in {"gibson", "in-fusion", "infusion"}:
        v = sanitize_sequence(vector)
        i = sanitize_sequence(insert)
        k = _overlap_len(v, i, min_overlap=min_overlap)
        if k < min_overlap:
            ok = False
            messages.append(f"Insufficient overlap: found {k}bp, need >= {min_overlap}bp")
        else:
            messages.append(f"Overlap OK: {k}bp")
        return {"mode": mode, "ok": ok, "messages": messages, "checks": {"overlap_bp": k, "required_overlap_bp": min_overlap}}

    return {"mode": mode, "ok": False, "messages": ["Unsupported mode"], "checks": {}}


def _end_object(enzyme: str) -> Dict[str, str]:
    if enzyme not in ENZYME_STICKY_ENDS:
        raise ValueError(f"No sticky-end model for enzyme {enzyme}")
    meta = ENZYME_STICKY_ENDS[enzyme]
    return {"enzyme": enzyme, "overhang": meta["overhang"], "polarity": meta["polarity"]}


def _end_from_sequence(seq: str, enzyme: str, side: str = "left") -> Dict[str, Any]:
    if enzyme not in ENZYMES or enzyme not in ENZYME_STICKY_ENDS:
        raise ValueError(f"Unsupported enzyme for sequence-derived ends: {enzyme}")
    sequence = sanitize_sequence(seq)
    site, cut_offset = ENZYMES[enzyme]
    starts = find_all_occurrences(sequence, site, circular=True)
    if not starts:
        raise ValueError(f"Enzyme site {enzyme}/{site} not found in sequence")
    # Use first site for left and last site for right to emulate fragment boundaries.
    s = starts[0] if side == "left" else starts[-1]
    cut = (s + cut_offset) % len(sequence)
    model = ENZYME_STICKY_ENDS[enzyme]
    ov_len = len(model["overhang"])
    if model["polarity"] == "5prime":
        ov = _slice_circular(sequence, cut, ov_len)
    else:
        ov = _slice_circular(sequence, cut - ov_len, ov_len)
    return {"enzyme": enzyme, "overhang": ov, "polarity": model["polarity"], "cut_index_0based": cut, "site_start_0based": s}


def _window_circular(seq: str, boundary: int, left: int = 12, right: int = 12) -> str:
    n = len(seq)
    if n == 0:
        return ""
    out = []
    for i in range(left + right):
        out.append(seq[(boundary - left + i) % n])
    return "".join(out)


def _junction_integrity(
    sequence: str,
    boundary: int,
    enzyme_a: str,
    enzyme_b: str,
    label: str,
) -> Dict[str, Any]:
    win = _window_circular(sequence, boundary, left=16, right=16)
    scar = _window_circular(sequence, boundary, left=4, right=4)
    sites = []
    for enz in (enzyme_a, enzyme_b):
        site = ENZYMES.get(enz, ("", 0))[0]
        if site:
            sites.append({"enzyme": enz, "site": site, "recreated": site in win})
    recreated = [s["enzyme"] for s in sites if s["recreated"]]
    return {
        "label": label,
        "boundary_index_0based": boundary,
        "scar_8bp": scar,
        "window_32bp": win,
        "expected_sites": sites,
        "recreated_sites": recreated,
    }


def _annotate_ligation_products(
    products: List[Dict[str, Any]],
    vector_len: int,
    insert_len: int,
    vector_left_enzyme: str,
    vector_right_enzyme: str,
    insert_left_enzyme: str,
    insert_right_enzyme: str,
) -> None:
    for p in products:
        cls = str(p.get("class", ""))
        seq = str(p.get("sequence", ""))
        if not seq:
            continue
        if cls == "desired_insert":
            orient = str(p.get("orientation", "forward"))
            if orient == "forward":
                j1 = _junction_integrity(seq, vector_len, vector_left_enzyme, insert_right_enzyme, "vector->insert")
                j2 = _junction_integrity(seq, vector_len + insert_len, insert_left_enzyme, vector_right_enzyme, "insert->vector")
            else:
                j1 = _junction_integrity(seq, vector_len, vector_left_enzyme, insert_left_enzyme, "vector->insert(rev)")
                j2 = _junction_integrity(seq, vector_len + insert_len, insert_right_enzyme, vector_right_enzyme, "insert->vector(rev)")
            p["junction_integrity"] = [j1, j2]
            mod3 = insert_len % 3
            p["fusion_frame"] = {
                "insert_len_mod3": mod3,
                "status": "in_frame" if mod3 == 0 else "frameshift_risk",
            }
        elif cls == "vector_self_ligation":
            p["junction_integrity"] = [
                _junction_integrity(seq, vector_len, vector_left_enzyme, vector_right_enzyme, "vector_religation")
            ]
        elif cls in {"insert_self_ligation", "insert_concatemer"}:
            p["junction_integrity"] = [
                _junction_integrity(seq, insert_len, insert_left_enzyme, insert_right_enzyme, "insert_religation")
            ]


def ligation_simulate(
    vector_sequence: str,
    insert_sequence: str,
    vector_left_enzyme: str,
    vector_right_enzyme: str,
    insert_left_enzyme: str,
    insert_right_enzyme: str,
    derive_from_sequence: bool = False,
    include_byproducts: bool = True,
    temp_c: float = 16.0,
    ligase_units: float = 1.0,
    vector_insert_ratio: float = 1.0,
    dna_ng: float = 100.0,
    phosphatase_treated_vector: bool = False,
    star_activity_level: float = 0.0,
) -> Dict[str, Any]:
    v = sanitize_sequence(vector_sequence)
    i = sanitize_sequence(insert_sequence)

    if derive_from_sequence:
        v_left = _end_from_sequence(v, vector_left_enzyme, "left")
        v_right = _end_from_sequence(v, vector_right_enzyme, "right")
        i_left = _end_from_sequence(i, insert_left_enzyme, "left")
        i_right = _end_from_sequence(i, insert_right_enzyme, "right")
    else:
        v_left = _end_object(vector_left_enzyme)
        v_right = _end_object(vector_right_enzyme)
        i_left = _end_object(insert_left_enzyme)
        i_right = _end_object(insert_right_enzyme)

    def comp(a: str, b: str) -> bool:
        return is_complementary(a, b)

    forward_ok = comp(v_left["overhang"], i_right["overhang"]) and comp(i_left["overhang"], v_right["overhang"])
    reverse_ok = comp(v_left["overhang"], i_left["overhang"]) and comp(i_right["overhang"], v_right["overhang"])

    products = []
    if forward_ok:
        products.append(
            {
                "class": "desired_insert",
                "orientation": "forward",
                "length": len(v) + len(i),
                "junctions": [
                    {"left": v_left["overhang"], "right": i_right["overhang"]},
                    {"left": i_left["overhang"], "right": v_right["overhang"]},
                ],
                "sequence": v + i,
                "rank_score": 100,
            }
        )
    if reverse_ok:
        i_rev = revcomp(i)
        products.append(
            {
                "class": "desired_insert",
                "orientation": "reverse",
                "length": len(v) + len(i),
                "junctions": [
                    {"left": v_left["overhang"], "right": i_left["overhang"]},
                    {"left": i_right["overhang"], "right": v_right["overhang"]},
                ],
                "sequence": v + i_rev,
                "rank_score": 95,
            }
        )

    if include_byproducts:
        # Vector recircularization
        if (not phosphatase_treated_vector) and comp(v_left["overhang"], v_right["overhang"]):
            products.append(
                {
                    "class": "vector_self_ligation",
                    "orientation": "vector_only",
                    "length": len(v),
                    "junctions": [{"left": v_left["overhang"], "right": v_right["overhang"]}],
                    "sequence": v,
                    "rank_score": 70,
                }
            )
        # Insert self-ligation
        if comp(i_left["overhang"], i_right["overhang"]):
            products.append(
                {
                    "class": "insert_self_ligation",
                    "orientation": "insert_only",
                    "length": len(i),
                    "junctions": [{"left": i_left["overhang"], "right": i_right["overhang"]}],
                    "sequence": i,
                    "rank_score": 60,
                }
            )
        # Insert concatemer (two-copy) in forward orientation
        if comp(i_left["overhang"], i_right["overhang"]):
            products.append(
                {
                    "class": "insert_concatemer",
                    "orientation": "concatemer_forward",
                    "length": len(i) * 2,
                    "junctions": [{"left": i_left["overhang"], "right": i_right["overhang"]}],
                    "sequence": i + i,
                    "rank_score": 50,
                }
            )

    _annotate_ligation_products(
        products,
        vector_len=len(v),
        insert_len=len(i),
        vector_left_enzyme=vector_left_enzyme,
        vector_right_enzyme=vector_right_enzyme,
        insert_left_enzyme=insert_left_enzyme,
        insert_right_enzyme=insert_right_enzyme,
    )

    messages = []
    risk_flags = []
    if not products:
        messages.append("No compatible ligation orientation found with provided ends")
    else:
        messages.append(f"Found {len(products)} compatible ligation product(s)")
    if phosphatase_treated_vector:
        messages.append("Vector phosphatase treatment enabled: vector self-ligation suppressed")
    if float(star_activity_level) > 0.25:
        risk_flags.append("star_activity_risk")
        messages.append("Elevated star-activity risk may increase undesired byproducts")

    def condition_factor(product: Dict[str, Any]) -> float:
        product_class = str(product.get("class", ""))
        # Coarse heuristic: ligation efficiency is best near 16C for sticky-end products.
        temp_opt = max(0.2, 1.0 - abs(float(temp_c) - 16.0) / 28.0)
        ligase_factor = max(0.2, min(2.0, float(ligase_units) / 1.0))
        dna_factor = max(0.3, min(1.7, float(dna_ng) / 100.0))
        ratio = max(0.05, float(vector_insert_ratio))
        star = max(0.0, min(1.0, float(star_activity_level)))
        # Penalize joins with mixed overhang polarity.
        if product_class == "desired_insert":
            if str(product.get("orientation")) == "forward":
                pols = [(v_left["polarity"], i_right["polarity"]), (i_left["polarity"], v_right["polarity"])]
            elif str(product.get("orientation")) == "reverse":
                pols = [(v_left["polarity"], i_left["polarity"]), (i_right["polarity"], v_right["polarity"])]
            else:
                pols = []
            if pols:
                matches = sum(1 for a, b in pols if a == b)
                polarity_factor = 0.65 + 0.35 * (matches / len(pols))
            else:
                polarity_factor = 1.0
        else:
            polarity_factor = 1.0
        if product_class == "desired_insert":
            ratio_factor = max(0.3, min(1.8, ratio))
            base = 1.0 * (1.0 - 0.35 * star)
        elif product_class == "vector_self_ligation":
            ratio_factor = max(0.2, min(2.2, 1.0 / ratio))
            base = 0.55 * (1.0 + 0.8 * star)
        elif product_class == "insert_self_ligation":
            ratio_factor = max(0.3, min(2.0, ratio * 0.8))
            base = 0.45 * (1.0 + 0.7 * star)
        else:  # concatemer and other byproducts
            ratio_factor = max(0.3, min(2.5, ratio * 1.1))
            base = 0.35 * (1.0 + 0.9 * star)
        return base * temp_opt * ligase_factor * dna_factor * ratio_factor * polarity_factor

    raw_scores = []
    for p in products:
        s = float(p.get("rank_score", 0)) * condition_factor(p)
        p["condition_adjusted_score"] = round(s, 3)
        raw_scores.append(max(0.0, s))
    score_sum = sum(raw_scores)
    if score_sum > 0:
        for p, s in zip(products, raw_scores):
            p["predicted_probability"] = round(s / score_sum, 4)
    else:
        for p in products:
            p["predicted_probability"] = 0.0

    products.sort(key=lambda p: (-float(p.get("predicted_probability", 0.0)), -float(p.get("condition_adjusted_score", 0.0)), int(p.get("length", 0))))
    return {
        "vector_ends": {"left": v_left, "right": v_right},
        "insert_ends": {"left": i_left, "right": i_right},
        "derive_from_sequence": derive_from_sequence,
        "include_byproducts": include_byproducts,
        "reaction_conditions": {
            "temp_c": float(temp_c),
            "ligase_units": float(ligase_units),
            "vector_insert_ratio": float(vector_insert_ratio),
            "dna_ng": float(dna_ng),
            "phosphatase_treated_vector": bool(phosphatase_treated_vector),
            "star_activity_level": float(star_activity_level),
        },
        "risk_flags": risk_flags,
        "forward_compatible": forward_ok,
        "reverse_compatible": reverse_ok,
        "products": products,
        "messages": messages,
    }


def in_fusion_assemble(fragments: List[str], min_overlap: int = 15, circular: bool = False) -> Dict[str, Any]:
    if len(fragments) < 2:
        raise ValueError("Need at least two fragments")
    frags = [parse_plain_sequence(x) for x in fragments]
    assembled = frags[0]
    joins: List[Dict[str, Any]] = []
    for i in range(1, len(frags)):
        a = assembled
        b = frags[i]
        max_k = min(len(a), len(b))
        k_best = 0
        for k in range(max_k, min_overlap - 1, -1):
            if a[-k:] == b[:k]:
                k_best = k
                break
        if k_best < min_overlap:
            raise ValueError(f"Insufficient homology arm between fragment {i} and {i+1}")
        joins.append({"left_fragment": i, "right_fragment": i + 1, "homology_bp": k_best})
        assembled = a + b[k_best:]

    circular_join = 0
    if circular:
        max_k = min(len(assembled), len(frags[0]))
        for k in range(max_k, min_overlap - 1, -1):
            if assembled[-k:] == frags[0][:k]:
                circular_join = k
                assembled = assembled[:-k]
                break
        if circular_join < min_overlap:
            raise ValueError("Insufficient closing homology arm for circular In-Fusion")

    return {
        "fragment_count": len(frags),
        "joins": joins,
        "closing_homology_bp": circular_join,
        "assembled_length": len(assembled),
        "assembled_sequence": assembled,
        "topology": "circular" if circular else "linear",
    }


def overlap_extension_pcr(fragment_a: str, fragment_b: str, min_overlap: int = 18) -> Dict[str, Any]:
    a = parse_plain_sequence(fragment_a)
    b = parse_plain_sequence(fragment_b)
    max_k = min(len(a), len(b))
    best = 0
    for k in range(max_k, min_overlap - 1, -1):
        if a[-k:] == b[:k]:
            best = k
            break
    if best < min_overlap:
        raise ValueError("No sufficient overlap for overlap-extension PCR")
    product = a + b[best:]
    return {
        "overlap_bp": best,
        "product_length": len(product),
        "product_sequence": product,
    }


def project_history_graph(name: str) -> Dict[str, Any]:
    doc = load_project(name)
    hist = doc.get("history", [])
    nodes = []
    edges = []
    prev = None
    for i, snap in enumerate(hist):
        nodes.append({"id": i, "label": f"v{i+1}", "size": len(str(snap))})
        if prev is not None:
            edges.append({"from": prev, "to": i})
        prev = i
    return {"project_name": name, "node_count": len(nodes), "nodes": nodes, "edges": edges}


def project_history_svg(name: str) -> Dict[str, Any]:
    g = project_history_graph(name)
    nodes = g["nodes"]
    edges = g["edges"]
    w = max(480, 140 * max(1, len(nodes)))
    h = 180
    y = 90
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    if nodes:
        gap = w // (len(nodes) + 1)
        coords = {}
        for i, n in enumerate(nodes, start=1):
            x = i * gap
            coords[n["id"]] = x
        for e in edges:
            x1 = coords[e["from"]]
            x2 = coords[e["to"]]
            lines.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#64748b" stroke-width="2"/>')
        for n in nodes:
            x = coords[n["id"]]
            r = max(12, min(26, int(8 + (n["size"] ** 0.5))))
            t = 0.0 if len(nodes) <= 1 else (n["id"] / max(1, len(nodes) - 1))
            rr = int(16 + 180 * t)
            gg = int(118 - 48 * t)
            bb = int(110 - 30 * t)
            fill = f"rgb({rr},{gg},{bb})"
            lines.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" opacity="0.9"/>')
            lines.append(f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="11" fill="white">{n["label"]}</text>')
    lines.append("</svg>")
    return {"project_name": name, "svg": "\n".join(lines), **g}


def auto_annotate(record: SequenceRecord) -> Dict[str, Any]:
    seq = record.sequence
    circular = record.topology == "circular"
    rows: List[Dict[str, Any]] = []
    for patt in ANNOTATION_PATTERNS:
        motif = patt["motif"]
        hits = find_all_occurrences(seq, motif, circular=circular)
        for h in hits:
            start = h + 1
            end = h + len(motif)
            if end > record.length and circular:
                end = end - record.length
            rows.append(
                {
                    "label": patt["label"],
                    "type": patt["type"],
                    "motif": motif,
                    "start_1based": start,
                    "end_1based": end,
                }
            )
    # Add ORF-derived CDS annotations for practical coding-region discovery.
    for i, (start, end, frame, protein) in enumerate(record.find_orfs(min_aa_len=40), start=1):
        rows.append(
            {
                "label": f"Auto_CDS_{i}",
                "type": "CDS",
                "motif": "ORF",
                "start_1based": start,
                "end_1based": end,
                "frame": frame,
                "aa_len": len(protein),
            }
        )
    rows.sort(key=lambda x: x["start_1based"])
    return {"count": len(rows), "annotations": rows}


def _overlap_len(a: str, b: str, min_overlap: int) -> int:
    max_k = min(len(a), len(b))
    for k in range(max_k, min_overlap - 1, -1):
        if a[-k:] == b[:k]:
            return k
    return 0


def contig_assemble(reads: List[str], min_overlap: int = 20) -> Dict[str, Any]:
    seqs = [parse_plain_sequence(r) for r in reads if str(r).strip()]
    if len(seqs) < 2:
        raise ValueError("Need at least two reads")
    merged_steps: List[Dict[str, Any]] = []
    while len(seqs) > 1:
        best_i = best_j = -1
        best_k = 0
        for i in range(len(seqs)):
            for j in range(len(seqs)):
                if i == j:
                    continue
                k = _overlap_len(seqs[i], seqs[j], min_overlap=min_overlap)
                if k > best_k:
                    best_i, best_j, best_k = i, j, k
        if best_k < min_overlap:
            break
        a = seqs[best_i]
        b = seqs[best_j]
        merged = a + b[best_k:]
        merged_steps.append({"left_idx": best_i, "right_idx": best_j, "overlap_bp": best_k, "merged_length": len(merged)})
        for idx in sorted([best_i, best_j], reverse=True):
            del seqs[idx]
        seqs.append(merged)
    seqs.sort(key=len, reverse=True)
    return {
        "input_reads": len(reads),
        "contig_count": len(seqs),
        "largest_contig_length": len(seqs[0]) if seqs else 0,
        "steps": merged_steps,
        "contigs": seqs,
    }


def multi_align_to_reference(sequences: List[str]) -> Dict[str, Any]:
    seqs = [parse_plain_sequence(s) for s in sequences if str(s).strip()]
    if len(seqs) < 2:
        raise ValueError("Need at least two sequences")
    ref = seqs[0]
    results = []
    for idx, s in enumerate(seqs[1:], start=2):
        aln = needleman_wunsch(ref, s)
        results.append(
            {
                "sequence_index": idx,
                "score": aln["score"],
                "identity_pct": aln["identity_pct"],
                "aligned_ref": aln["aligned_a"],
                "aligned_query": aln["aligned_b"],
            }
        )
    return {"reference_length": len(ref), "sequence_count": len(seqs), "pairwise_to_reference": results}


def _merge_gapped_reference(
    old_ref: str,
    old_rows: List[str],
    new_ref: str,
    new_row: str,
) -> Tuple[List[str], str]:
    i = j = 0
    merged_rows = ["" for _ in old_rows]
    merged_new = ""
    while i < len(old_ref) or j < len(new_ref):
        co = old_ref[i] if i < len(old_ref) else None
        cn = new_ref[j] if j < len(new_ref) else None
        if co is None:
            for k in range(len(merged_rows)):
                merged_rows[k] += "-"
            merged_new += new_row[j]
            j += 1
            continue
        if cn is None:
            for k in range(len(merged_rows)):
                merged_rows[k] += old_rows[k][i]
            merged_new += "-"
            i += 1
            continue
        if co == cn:
            for k in range(len(merged_rows)):
                merged_rows[k] += old_rows[k][i]
            merged_new += new_row[j]
            i += 1
            j += 1
        elif co == "-":
            for k in range(len(merged_rows)):
                merged_rows[k] += old_rows[k][i]
            merged_new += "-"
            i += 1
        elif cn == "-":
            for k in range(len(merged_rows)):
                merged_rows[k] += "-"
            merged_new += new_row[j]
            j += 1
        else:
            for k in range(len(merged_rows)):
                merged_rows[k] += old_rows[k][i]
            merged_new += new_row[j]
            i += 1
            j += 1
    return merged_rows, merged_new


def progressive_msa(sequences: List[str]) -> Dict[str, Any]:
    seqs = [parse_plain_sequence(s) for s in sequences if str(s).strip()]
    if len(seqs) < 2:
        raise ValueError("Need at least two sequences")
    ref = seqs[0]
    aligned_rows = [ref]
    ref_gapped = ref
    for s in seqs[1:]:
        aln = needleman_wunsch(ref, s)
        new_ref = aln["aligned_a"]
        new_seq = aln["aligned_b"]
        aligned_rows, merged_new = _merge_gapped_reference(ref_gapped, aligned_rows, new_ref, new_seq)
        aligned_rows.append(merged_new)
        ref_gapped = aligned_rows[0]
    col_count = len(aligned_rows[0]) if aligned_rows else 0
    return {"method": "progressive", "sequence_count": len(aligned_rows), "columns": col_count, "alignment": aligned_rows}


def _parse_fasta_text(text: str) -> List[str]:
    rows: List[str] = []
    cur = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith(">"):
            if cur:
                rows.append("".join(cur))
                cur = []
        else:
            cur.append(s)
    if cur:
        rows.append("".join(cur))
    return rows


def external_msa(method: str, sequences: List[str]) -> Dict[str, Any]:
    seqs = [parse_plain_sequence(s) for s in sequences if str(s).strip()]
    if len(seqs) < 2:
        raise ValueError("Need at least two sequences")
    bin_map = {
        "clustalw": "clustalw2",
        "clustalw2": "clustalw2",
        "mafft": "mafft",
        "muscle": "muscle",
        "tcoffee": "t_coffee",
        "t-coffee": "t_coffee",
    }
    method = method.lower()
    bin_name = bin_map.get(method, method)
    if not shutil.which(bin_name):
        return {"fallback": True, "reason": f"{bin_name} not found", **progressive_msa(seqs)}

    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / "in.fa"
        inp.write_text("\n".join([f">seq{i+1}\n{s}" for i, s in enumerate(seqs)]) + "\n", encoding="utf-8")
        if method.startswith("clustalw"):
            out = Path(td) / "out.aln"
            cmd = [bin_name, f"-INFILE={inp}", "-OUTPUT=FASTA", f"-OUTFILE={out}"]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            aligned = _parse_fasta_text(out.read_text(encoding="utf-8"))
        elif method == "mafft":
            cmd = [bin_name, "--auto", str(inp)]
            r = subprocess.run(cmd, check=True, capture_output=True, text=True)
            aligned = _parse_fasta_text(r.stdout)
        elif method == "muscle":
            out = Path(td) / "out.fa"
            cmd = [bin_name, "-align", str(inp), "-output", str(out)]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            aligned = _parse_fasta_text(out.read_text(encoding="utf-8"))
        elif method in {"tcoffee", "t-coffee"}:
            cmd = [bin_name, "-in", str(inp), "-output=fasta_aln"]
            r = subprocess.run(cmd, check=True, capture_output=True, text=True)
            aligned = _parse_fasta_text(r.stdout)
            if not aligned:
                fallback_out = Path(td) / "in.fa.aln"
                if fallback_out.exists():
                    aligned = _parse_fasta_text(fallback_out.read_text(encoding="utf-8"))
            if not aligned:
                raise ValueError("t_coffee produced no FASTA alignment output")
        else:
            raise ValueError(f"Unsupported MSA method: {method}")
    return {"method": method, "sequence_count": len(aligned), "columns": len(aligned[0]) if aligned else 0, "alignment": aligned}


def alignment_consensus(alignment: List[str]) -> Dict[str, Any]:
    rows = [str(r) for r in alignment if str(r)]
    if not rows:
        raise ValueError("Alignment is empty")
    width = len(rows[0])
    if any(len(r) != width for r in rows):
        raise ValueError("Alignment rows must have equal length")
    consensus_chars = []
    conservation = []
    for col in range(width):
        counts: Dict[str, int] = {}
        for r in rows:
            ch = r[col]
            counts[ch] = counts.get(ch, 0) + 1
        counts_nogap = {k: v for k, v in counts.items() if k != "-"}
        if counts_nogap:
            best = max(sorted(counts_nogap), key=lambda k: counts_nogap[k])
            consensus_chars.append(best)
            conservation.append(round(counts_nogap[best] / len(rows), 3))
        else:
            consensus_chars.append("-")
            conservation.append(0.0)
    identity_matrix = []
    for i in range(len(rows)):
        row = []
        for j in range(len(rows)):
            same = sum(1 for a, b in zip(rows[i], rows[j]) if a == b)
            row.append(round(same / width * 100.0, 2))
        identity_matrix.append(row)
    return {
        "row_count": len(rows),
        "columns": width,
        "consensus": "".join(consensus_chars),
        "conservation": conservation,
        "identity_matrix_pct": identity_matrix,
    }


def sequence_track_svg(
    record: SequenceRecord,
    start_1based: int = 1,
    end_1based: int | None = None,
    frame: int = 1,
) -> Dict[str, Any]:
    if end_1based is None:
        end_1based = min(record.length, start_1based + 299)
    if start_1based < 1 or end_1based > record.length or start_1based > end_1based:
        raise ValueError("Invalid track window")
    if frame not in (1, 2, 3):
        raise ValueError("Frame must be 1,2,3")

    seq = record.sequence[start_1based - 1 : end_1based]
    width = 1200
    left = 40
    usable = width - 2 * left
    h = 260
    y_axis = 90

    def x_for_pos(pos_1based: int) -> float:
        frac = (pos_1based - start_1based) / max(1, (end_1based - start_1based))
        return left + frac * usable

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    lines.append(f'<text x="{left}" y="24" font-size="14" font-family="Menlo, monospace" fill="#0f172a">{record.name}  {start_1based}..{end_1based}</text>')
    lines.append(f'<line x1="{left}" y1="{y_axis}" x2="{width-left}" y2="{y_axis}" stroke="#0f172a" stroke-width="2"/>')

    feature_colors = {
        "cds": "#2563eb",
        "gene": "#dc2626",
        "promoter": "#16a34a",
        "rbs": "#0d9488",
        "terminator": "#d97706",
        "misc_feature": "#7c3aed",
    }

    def parse_loc(loc: str) -> Tuple[int, int, int]:
        loc_s = loc.strip()
        strand = -1 if "complement" in loc_s.lower() else 1
        nums = [int(x) for x in "".join(ch if ch.isdigit() else " " for ch in loc_s).split()]
        if len(nums) < 2:
            return 0, 0, strand
        a, b = nums[0], nums[-1]
        if a > b:
            a, b = b, a
        return a, b, strand

    for i, f in enumerate(record.features):
        a, b, strand = parse_loc(f.location)
        if a <= 0 or b <= 0:
            continue
        if b < start_1based or a > end_1based:
            continue
        fa = max(a, start_1based)
        fb = min(b, end_1based)
        x1 = x_for_pos(fa)
        x2 = x_for_pos(fb)
        color = feature_colors.get(f.key.lower(), "#475569")
        width_f = max(2.0, x2 - x1)
        lines.append(
            f'<rect x="{x1:.2f}" y="{y_axis-22}" width="{width_f:.2f}" height="14" rx="3" fill="{color}" opacity="0.9" '
            f'data-feature-index="{i}" data-feature-start="{fa}" data-feature-end="{fb}" class="feature-segment"/>'
        )
        # Strand arrow marker.
        if width_f >= 10:
            if strand > 0:
                ax = x2
                pts = f"{ax-8:.2f},{y_axis-22:.2f} {ax:.2f},{y_axis-15:.2f} {ax-8:.2f},{y_axis-8:.2f}"
            else:
                ax = x1
                pts = f"{ax+8:.2f},{y_axis-22:.2f} {ax:.2f},{y_axis-15:.2f} {ax+8:.2f},{y_axis-8:.2f}"
            lines.append(
                f'<polygon points="{pts}" fill="#0f172a" opacity="0.75" '
                f'data-feature-index="{i}" class="feature-arrow"/>'
            )
        label = f.qualifiers.get("label") or f.qualifiers.get("gene") or f.key
        extra = ""
        if f.key.lower() == "cds":
            phase = (a - 1) % 3
            extra = f" phase={phase}"
        lines.append(
            f'<text x="{x1:.2f}" y="{y_axis-28}" font-size="10" font-family="Menlo, monospace" fill="#111827" '
            f'data-feature-index="{i}" class="feature-label">{label}{extra}</text>'
        )

    # Translation lane for selected frame.
    frame_offset = frame - 1
    cds_seq = record.sequence[start_1based - 1 + frame_offset : end_1based]
    aa = record.translate(frame=frame, to_stop=False)
    local_aa = []
    start_codon_index = (start_1based - 1 + frame_offset) // 3
    aa_count = len(cds_seq) // 3
    for i in range(aa_count):
        idx = start_codon_index + i
        if idx < len(aa):
            local_aa.append(aa[idx])
        else:
            local_aa.append("X")

    y_aa = 150
    lines.append(f'<text x="{left}" y="{y_aa-12}" font-size="12" font-family="Menlo, monospace" fill="#334155">Translation frame {frame}</text>')
    for i, residue in enumerate(local_aa):
        codon_start = start_1based + frame_offset + i * 3
        codon_end = codon_start + 2
        if codon_end > end_1based:
            break
        x1 = x_for_pos(codon_start)
        x2 = x_for_pos(codon_end)
        mid = (x1 + x2) / 2
        fill = "#fca5a5" if residue == "*" else "#dbeafe"
        codon = record.sequence[codon_start - 1 : codon_end]
        lines.append(
            f'<rect x="{x1:.2f}" y="{y_aa}" width="{max(4.0, x2-x1):.2f}" height="18" rx="2" fill="{fill}" stroke="#93c5fd" stroke-width="0.5" '
            f'data-codon-start="{codon_start}" data-codon-end="{codon_end}" data-residue="{residue}" class="codon-cell">'
            f'<title>codon {codon_start}-{codon_end}: {codon} -> {residue}</title></rect>'
        )
        lines.append(f'<text x="{mid:.2f}" y="{y_aa+13}" text-anchor="middle" font-size="10" font-family="Menlo, monospace" fill="#0f172a">{residue}</text>')

    # Nucleotide ruler
    y_nt = 210
    step = max(10, (end_1based - start_1based + 1) // 12)
    for p in range(start_1based, end_1based + 1, step):
        x = x_for_pos(p)
        lines.append(f'<line x1="{x:.2f}" y1="{y_nt-12}" x2="{x:.2f}" y2="{y_nt-6}" stroke="#334155" stroke-width="1"/>')
        lines.append(f'<text x="{x:.2f}" y="{y_nt}" text-anchor="middle" font-size="10" font-family="Menlo, monospace" fill="#334155">{p}</text>')

    lines.append("</svg>")
    return {"start_1based": start_1based, "end_1based": end_1based, "frame": frame, "svg": "\n".join(lines)}


def alignment_heatmap_svg(alignment: List[str]) -> Dict[str, Any]:
    c = alignment_consensus(alignment)
    matrix = c["identity_matrix_pct"]
    n = len(matrix)
    if n == 0:
        raise ValueError("Empty alignment")
    cell = 28
    margin = 70
    w = margin + n * cell + 30
    h = margin + n * cell + 30
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    for i in range(n):
        x = margin + i * cell + cell / 2
        y = margin - 10
        lines.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-size="10" font-family="Menlo, monospace" fill="#334155">S{i+1}</text>')
        x2 = margin - 12
        y2 = margin + i * cell + cell / 2 + 3
        lines.append(f'<text x="{x2:.1f}" y="{y2:.1f}" text-anchor="end" font-size="10" font-family="Menlo, monospace" fill="#334155">S{i+1}</text>')
    for i in range(n):
        for j in range(n):
            val = float(matrix[i][j])
            t = max(0.0, min(1.0, val / 100.0))
            # teal intensity from low->high identity
            r = int(240 - 170 * t)
            g = int(248 - 40 * t)
            b = int(255 - 120 * t)
            fill = f"rgb({r},{g},{b})"
            x = margin + j * cell
            y = margin + i * cell
            lines.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}" stroke="#cbd5e1" stroke-width="1"><title>S{i+1} vs S{j+1}: {val:.2f}%</title></rect>')
            if n <= 12:
                lines.append(f'<text x="{x+cell/2:.1f}" y="{y+cell/2+3:.1f}" text-anchor="middle" font-size="9" font-family="Menlo, monospace" fill="#0f172a">{val:.0f}</text>')
    lines.append('</svg>')
    return {"row_count": n, "svg": "\n".join(lines), "identity_matrix_pct": matrix}


def sequence_analytics_svg(
    record: SequenceRecord,
    start_1based: int = 1,
    end_1based: int | None = None,
    window: int = 120,
    step: int = 20,
) -> Dict[str, Any]:
    if end_1based is None:
        end_1based = record.length
    start_1based = max(1, int(start_1based))
    end_1based = min(record.length, int(end_1based))
    if start_1based > end_1based:
        raise ValueError("Invalid window range")
    window = max(30, int(window))
    step = max(5, int(step))
    seq = record.sequence[start_1based - 1 : end_1based]
    if len(seq) < 30:
        raise ValueError("Sequence range too short for analytics")

    xs: List[float] = []
    gc_pct: List[float] = []
    gc_skew: List[float] = []
    complexity: List[float] = []
    stop_density: List[float] = []
    points = 0
    for i in range(0, max(1, len(seq) - window + 1), step):
        wseq = seq[i : i + window]
        if len(wseq) < 20:
            continue
        center = start_1based + i + len(wseq) / 2.0
        points += 1
        g = wseq.count("G")
        c = wseq.count("C")
        gc = 100.0 * (g + c) / max(1, len(wseq))
        skew = (g - c) / max(1, g + c)
        kmers = {}
        for j in range(len(wseq) - 1):
            k = wseq[j : j + 2]
            kmers[k] = kmers.get(k, 0) + 1
        total_k = max(1, sum(kmers.values()))
        ent = 0.0
        for v in kmers.values():
            p = v / total_k
            ent -= p * math.log2(p)
        # Normalize dinucleotide entropy to [0,1], max log2(16)=4
        comp = min(1.0, max(0.0, ent / 4.0))
        stops = 0
        codons = max(1, len(wseq) // 3)
        for j in range(0, len(wseq) - 2, 3):
            if wseq[j : j + 3] in {"TAA", "TAG", "TGA"}:
                stops += 1
        sd = stops / codons

        xs.append(center)
        gc_pct.append(gc)
        gc_skew.append(skew)
        complexity.append(comp)
        stop_density.append(sd)

    if not xs:
        raise ValueError("No analytics points generated")

    width = 1200
    height = 420
    margin_l = 70
    margin_r = 24
    margin_t = 26
    panel_h = 82
    panel_gap = 12
    plot_w = width - margin_l - margin_r

    x_min = float(start_1based)
    x_max = float(end_1based)

    def x_for(p: float) -> float:
        return margin_l + (p - x_min) * plot_w / max(1.0, x_max - x_min)

    def to_poly(y_top: float, vals: List[float], vmin: float, vmax: float) -> str:
        pts = []
        rng = max(1e-9, vmax - vmin)
        for x, v in zip(xs, vals):
            y = y_top + panel_h - ((v - vmin) / rng) * panel_h
            pts.append(f"{x_for(x):.2f},{y:.2f}")
        return " ".join(pts)

    panels = [
        ("GC %", gc_pct, 0.0, 100.0, "#0ea5e9"),
        ("GC skew", gc_skew, -1.0, 1.0, "#f97316"),
        ("Complexity (entropy)", complexity, 0.0, 1.0, "#22c55e"),
        ("Stop codon density", stop_density, 0.0, max(0.25, max(stop_density) * 1.1), "#a855f7"),
    ]

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    lines.append(
        f'<text x="{margin_l}" y="18" font-size="13" font-family="Menlo, monospace" fill="#0f172a">'
        f'Sequence analytics: {record.name}  {start_1based}..{end_1based}</text>'
    )
    for idx, (label, vals, vmin, vmax, color) in enumerate(panels):
        y_top = margin_t + idx * (panel_h + panel_gap)
        lines.append(f'<rect x="{margin_l}" y="{y_top}" width="{plot_w}" height="{panel_h}" fill="#ffffff" stroke="#dbe5f3"/>')
        lines.append(f'<text x="8" y="{y_top + 16}" font-size="11" font-family="Menlo, monospace" fill="#334155">{label}</text>')
        for t in range(5):
            gx = margin_l + t * (plot_w / 4)
            lines.append(f'<line x1="{gx:.2f}" y1="{y_top}" x2="{gx:.2f}" y2="{y_top + panel_h}" stroke="#eef2f7" stroke-width="1"/>')
        lines.append(
            f'<polyline points="{to_poly(y_top, vals, vmin, vmax)}" fill="none" stroke="{color}" stroke-width="2">'
            f'<title>{label}</title></polyline>'
        )

    tick_y = margin_t + len(panels) * (panel_h + panel_gap) - panel_gap + 16
    for t in range(6):
        p = int(round(x_min + t * (x_max - x_min) / 5))
        x = x_for(float(p))
        lines.append(f'<line x1="{x:.2f}" y1="{tick_y-10}" x2="{x:.2f}" y2="{tick_y-4}" stroke="#334155"/>')
        lines.append(f'<text x="{x:.2f}" y="{tick_y+8}" text-anchor="middle" font-size="10" font-family="Menlo, monospace" fill="#334155">{p}</text>')
    lines.append("</svg>")

    return {
        "start_1based": start_1based,
        "end_1based": end_1based,
        "window": window,
        "step": step,
        "point_count": points,
        "gc_mean": round(sum(gc_pct) / len(gc_pct), 3),
        "gc_min": round(min(gc_pct), 3),
        "gc_max": round(max(gc_pct), 3),
        "svg": "\n".join(lines),
    }


def comparison_lens_svg(seq_a: str, seq_b: str, window: int = 60) -> Dict[str, Any]:
    a = sanitize_sequence(seq_a)
    b = sanitize_sequence(seq_b)
    if not a or not b:
        raise ValueError("seq_a and seq_b are required")
    window = max(20, int(window))
    aln = needleman_wunsch(a, b)
    aa = aln["aligned_a"]
    bb = aln["aligned_b"]
    n = len(aa)
    if n == 0:
        raise ValueError("Alignment empty")

    centers: List[int] = []
    divergence: List[float] = []
    confidence: List[float] = []
    for i in range(0, max(1, n - window + 1), max(5, window // 3)):
        wa = aa[i : i + window]
        wb = bb[i : i + window]
        if len(wa) < 10:
            continue
        mism = 0
        gap = 0
        valid = 0
        for ca, cb in zip(wa, wb):
            if ca == "-" or cb == "-":
                gap += 1
            else:
                valid += 1
                if ca != cb:
                    mism += 1
        total = max(1, len(wa))
        div = (mism + gap) / total
        conf = max(0.0, min(1.0, 1.0 - div))
        centers.append(i + len(wa) // 2 + 1)
        divergence.append(div)
        confidence.append(conf)

    width = 1200
    height = 260
    margin_l = 70
    margin_r = 30
    margin_t = 26
    plot_h = 170
    plot_w = width - margin_l - margin_r

    def x_for(p: float) -> float:
        return margin_l + (p - 1.0) * plot_w / max(1.0, n - 1.0)

    def y_for(v: float) -> float:
        return margin_t + plot_h - v * plot_h

    div_pts = " ".join(f"{x_for(c):.2f},{y_for(d):.2f}" for c, d in zip(centers, divergence))
    conf_pts = " ".join(f"{x_for(c):.2f},{y_for(cf):.2f}" for c, cf in zip(centers, confidence))

    idx_sorted = sorted(range(len(divergence)), key=lambda i: divergence[i], reverse=True)
    hotspots = []
    for i in idx_sorted[:5]:
        center = centers[i]
        s = max(1, center - window // 2)
        e = min(n, center + window // 2)
        hotspots.append({"start_aln_1based": s, "end_aln_1based": e, "divergence": round(divergence[i], 4)})

    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    lines.append(f'<text x="{margin_l}" y="18" font-size="13" font-family="Menlo, monospace" fill="#0f172a">Comparison lens (alignment length={n})</text>')
    lines.append(f'<rect x="{margin_l}" y="{margin_t}" width="{plot_w}" height="{plot_h}" fill="#ffffff" stroke="#dbe5f3"/>')
    for t in range(5):
        gy = margin_t + t * (plot_h / 4)
        lines.append(f'<line x1="{margin_l}" y1="{gy:.2f}" x2="{margin_l+plot_w}" y2="{gy:.2f}" stroke="#eef2f7"/>')
    lines.append(f'<polyline points="{div_pts}" fill="none" stroke="#ef4444" stroke-width="2"><title>Divergence</title></polyline>')
    lines.append(f'<polyline points="{conf_pts}" fill="none" stroke="#22c55e" stroke-width="2"><title>Confidence proxy</title></polyline>')
    for hs in hotspots:
        x1 = x_for(hs["start_aln_1based"])
        x2 = x_for(hs["end_aln_1based"])
        lines.append(
            f'<rect x="{x1:.2f}" y="{margin_t}" width="{max(1.0, x2-x1):.2f}" height="{plot_h}" fill="#fecaca" opacity="0.22">'
            f'<title>Hotspot {hs["start_aln_1based"]}-{hs["end_aln_1based"]}: div={hs["divergence"]}</title></rect>'
        )
    lines.append(f'<text x="{margin_l}" y="{margin_t+plot_h+18}" font-size="11" font-family="Menlo, monospace" fill="#334155">Red: divergence, Green: confidence proxy</text>')
    lines.append("</svg>")
    return {
        "alignment_length": n,
        "identity_pct": aln.get("identity_pct", 0.0),
        "window": window,
        "hotspots": hotspots,
        "svg": "\n".join(lines),
    }


def project_path(name: str) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid project name")
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    return PROJECTS_DIR / f"{safe}.json"


def save_project(payload: Dict[str, Any]) -> Dict[str, Any]:
    rec = parse_record(payload)
    name = str(payload.get("project_name") or rec.name).strip()
    p = project_path(name)
    src_format = infer_source_format(str(payload.get("content", "")))
    canon = record_to_canonical(rec, source_format=src_format, source_id=name)
    doc = {
        "project_name": name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "name": rec.name,
        "topology": rec.topology,
        "content": f">{rec.name}\n{rec.sequence}",
        "notes": str(payload.get("notes", "")),
        "history": payload.get("history", []),
        "features": features_to_dict(rec.features),
        "canonical_record": canon,
    }
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    append_audit_event(
        COLLAB_ROOT,
        project_name=name,
        action="project_save",
        actor=str(payload.get("actor", "system")),
        details={"path": str(p), "length": rec.length, "feature_count": len(rec.features)},
    )
    return {"saved": True, "project_name": name, "path": str(p)}


def load_project(name: str) -> Dict[str, Any]:
    p = project_path(name)
    if not p.exists():
        raise ValueError("Project not found")
    doc = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(doc.get("canonical_record"), dict):
        try:
            rec = parse_record(
                {
                    "name": doc.get("name", doc.get("project_name", "Untitled")),
                    "topology": doc.get("topology", "linear"),
                    "content": doc.get("content", ""),
                    "features": doc.get("features", []),
                }
            )
            doc["canonical_record"] = record_to_canonical(
                rec,
                source_format=infer_source_format(str(doc.get("content", ""))),
                source_id=str(doc.get("project_name", name)),
            )
        except Exception:
            pass
    return doc


def list_projects() -> Dict[str, Any]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(PROJECTS_DIR.glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
            rows.append(
                {
                    "project_name": doc.get("project_name", p.stem),
                    "updated_at": doc.get("updated_at", ""),
                    "path": str(p),
                }
            )
        except Exception:
            rows.append({"project_name": p.stem, "updated_at": "", "path": str(p)})
    return {"count": len(rows), "projects": rows}


def delete_project(name: str) -> Dict[str, Any]:
    p = project_path(name)
    if not p.exists():
        raise ValueError("Project not found")
    p.unlink()
    append_audit_event(COLLAB_ROOT, project_name=name, action="project_delete", actor="system", details={})
    return {"deleted": True, "project_name": name}


def collection_path(name: str) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid collection name")
    COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    return COLLECTIONS_DIR / f"{safe}.json"


def save_collection(name: str, project_names: List[str], notes: str = "") -> Dict[str, Any]:
    clean = sorted(set([str(x).strip() for x in project_names if str(x).strip()]))
    doc = {
        "collection_name": name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "projects": clean,
        "notes": notes,
    }
    p = collection_path(name)
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"saved": True, "collection_name": name, "count": len(clean), "path": str(p)}


def load_collection(name: str) -> Dict[str, Any]:
    p = collection_path(name)
    if not p.exists():
        raise ValueError("Collection not found")
    return json.loads(p.read_text(encoding="utf-8"))


def list_collections() -> Dict[str, Any]:
    COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(COLLECTIONS_DIR.glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
            rows.append(
                {
                    "collection_name": doc.get("collection_name", p.stem),
                    "updated_at": doc.get("updated_at", ""),
                    "count": len(doc.get("projects", [])),
                    "path": str(p),
                }
            )
        except Exception:
            rows.append({"collection_name": p.stem, "updated_at": "", "count": 0, "path": str(p)})
    return {"count": len(rows), "collections": rows}


def delete_collection(name: str) -> Dict[str, Any]:
    p = collection_path(name)
    if not p.exists():
        raise ValueError("Collection not found")
    p.unlink()
    return {"deleted": True, "collection_name": name}


def add_project_to_collection(name: str, project_name: str) -> Dict[str, Any]:
    doc = load_collection(name)
    projects = sorted(set([str(x) for x in doc.get("projects", [])] + [project_name]))
    return save_collection(name, projects, notes=str(doc.get("notes", "")))


def share_bundle_path(share_id: str) -> Path:
    safe = "".join(ch for ch in share_id if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid share id")
    SHARES_DIR.mkdir(parents=True, exist_ok=True)
    return SHARES_DIR / f"{safe}.json"


def create_share_bundle(project_names: List[str], collection_name: str = "", include_content: bool = True) -> Dict[str, Any]:
    names = sorted(set([str(x).strip() for x in project_names if str(x).strip()]))
    if not names and collection_name:
        c = load_collection(collection_name)
        names = [str(x) for x in c.get("projects", [])]
    if not names:
        raise ValueError("No projects selected for sharing")
    snapshot = []
    for name in names:
        doc = load_project(name)
        row = {
            "project_name": doc.get("project_name", name),
            "updated_at": doc.get("updated_at", ""),
            "name": doc.get("name", ""),
            "topology": doc.get("topology", ""),
        }
        if include_content:
            row["content"] = doc.get("content", "")
            row["features"] = doc.get("features", [])
        snapshot.append(row)
    share_id = uuid.uuid4().hex[:12]
    bundle = {
        "share_id": share_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "collection_name": collection_name,
        "project_count": len(snapshot),
        "projects": snapshot,
        "share_url_hint": f"/share/{share_id}",
    }
    p = share_bundle_path(share_id)
    p.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return {"created": True, "share_id": share_id, "path": str(p), "project_count": len(snapshot), "share_url_hint": bundle["share_url_hint"]}


def load_share_bundle(share_id: str) -> Dict[str, Any]:
    p = share_bundle_path(share_id)
    if not p.exists():
        raise ValueError("Share bundle not found")
    return json.loads(p.read_text(encoding="utf-8"))


def render_share_view_html(share_id: str) -> str:
    doc = load_share_bundle(share_id)
    projects = doc.get("projects", [])
    cards = []
    for p in projects:
        name = str(p.get("project_name", "unnamed"))
        topo = str(p.get("topology", ""))
        content = str(p.get("content", ""))
        seq = ""
        try:
            if content.startswith(">"):
                seq = parse_fasta(content).sequence
            elif content.lstrip().startswith("LOCUS"):
                seq = parse_genbank(content).sequence
            elif content.lstrip().startswith("ID"):
                seq = parse_embl(content).sequence
            else:
                seq = "".join(ch for ch in content.upper() if ch in {"A", "C", "G", "T", "N"})
        except Exception:
            seq = "".join(ch for ch in content.upper() if ch in {"A", "C", "G", "T", "N"})
        cards.append(
            f"""
            <article style="border:1px solid #d4d4d8;border-radius:10px;padding:10px;background:#fff">
              <h3 style="margin:0 0 6px 0;font-family:Menlo,monospace">{name}</h3>
              <div style="font-size:12px;color:#334155">topology: {topo} | length: {len(seq)} bp</div>
              <pre style="font-size:11px;background:#0f172a;color:#e2e8f0;padding:8px;border-radius:8px;overflow:auto">{seq[:500]}</pre>
            </article>
            """
        )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Genome Forge Share {share_id}</title></head>
<body style="margin:0;background:#f8fafc;color:#0f172a;font-family:system-ui,sans-serif">
<main style="max-width:1000px;margin:24px auto;padding:0 14px">
<h1 style="margin:0 0 8px 0">Shared Bundle {share_id}</h1>
<p style="margin:0 0 16px 0;color:#475569">Projects: {doc.get('project_count', len(projects))} | Created: {doc.get('created_at','')}</p>
<section style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px">
{''.join(cards)}
</section>
</main>
</body></html>"""


def features_to_dict(features: List[Feature]) -> List[Dict[str, Any]]:
    return [{"key": f.key, "location": f.location, "qualifiers": dict(f.qualifiers)} for f in features]


def enzyme_set_path(name: str) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid enzyme set name")
    ENZYME_SET_DIR.mkdir(parents=True, exist_ok=True)
    return ENZYME_SET_DIR / f"{safe}.json"


def save_enzyme_set(name: str, enzymes: List[str], notes: str = "") -> Dict[str, Any]:
    clean = [e for e in [str(x).strip() for x in enzymes] if e]
    unknown = [e for e in clean if e not in ENZYME_META and e not in ENZYMES]
    if unknown:
        raise ValueError(f"Unknown enzymes in set: {', '.join(sorted(set(unknown)))}")
    p = enzyme_set_path(name)
    doc = {
        "name": name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "enzymes": sorted(set(clean)),
        "notes": notes,
    }
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"saved": True, "name": name, "count": len(doc["enzymes"]), "path": str(p)}


def list_enzyme_sets() -> Dict[str, Any]:
    ENZYME_SET_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(ENZYME_SET_DIR.glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
            rows.append(
                {
                    "name": doc.get("name", p.stem),
                    "updated_at": doc.get("updated_at", ""),
                    "count": len(doc.get("enzymes", [])),
                    "path": str(p),
                }
            )
        except Exception:
            rows.append({"name": p.stem, "updated_at": "", "count": 0, "path": str(p)})
    for name, enzymes in sorted(BUILTIN_ENZYME_SETS.items()):
        rows.append(
            {
                "name": name,
                "updated_at": "builtin",
                "count": len(enzymes),
                "path": "builtin",
                "builtin": True,
            }
        )
    return {"count": len(rows), "sets": rows}


def load_enzyme_set(name: str) -> Dict[str, Any]:
    if name in BUILTIN_ENZYME_SETS:
        return {"name": name, "updated_at": "builtin", "enzymes": list(BUILTIN_ENZYME_SETS[name]), "builtin": True}
    p = enzyme_set_path(name)
    if not p.exists():
        raise ValueError("Enzyme set not found")
    return json.loads(p.read_text(encoding="utf-8"))


def delete_enzyme_set(name: str) -> Dict[str, Any]:
    if name in BUILTIN_ENZYME_SETS:
        raise ValueError("Cannot delete built-in enzyme set")
    p = enzyme_set_path(name)
    if not p.exists():
        raise ValueError("Enzyme set not found")
    p.unlink()
    return {"deleted": True, "name": name}


def list_predefined_enzyme_sets() -> Dict[str, Any]:
    rows = [{"name": k, "enzymes": v, "count": len(v)} for k, v in sorted(BUILTIN_ENZYME_SETS.items())]
    return {"count": len(rows), "sets": rows}


def resolve_enzymes(payload: Dict[str, Any]) -> List[str]:
    enzymes = payload.get("enzymes", [])
    if isinstance(enzymes, str):
        enzymes = [x.strip() for x in enzymes.split(",") if x.strip()]
    use_set = str(payload.get("enzyme_set", "")).strip()
    if use_set:
        doc = load_enzyme_set(use_set)
        enzymes = list(doc.get("enzymes", []))
    return [str(e).strip() for e in enzymes if str(e).strip()]


def annotation_db_path(name: str) -> Path:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_")).strip("_-")
    if not safe:
        raise ValueError("Invalid annotation db name")
    ANNOT_DB_DIR.mkdir(parents=True, exist_ok=True)
    return ANNOT_DB_DIR / f"{safe}.json"


def save_annotation_db(name: str, signatures: List[Dict[str, Any]]) -> Dict[str, Any]:
    p = annotation_db_path(name)
    cleaned = []
    for s in signatures:
        if not isinstance(s, dict):
            continue
        motif = sanitize_sequence(str(s.get("motif", "")))
        if not motif:
            continue
        cleaned.append(
            {
                "label": str(s.get("label", motif)),
                "type": str(s.get("type", "misc_feature")),
                "motif": motif,
            }
        )
    doc = {"name": name, "updated_at": datetime.now(timezone.utc).isoformat(), "signatures": cleaned}
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return {"saved": True, "name": name, "count": len(cleaned), "path": str(p)}


def list_annotation_dbs() -> Dict[str, Any]:
    ANNOT_DB_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(ANNOT_DB_DIR.glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
            rows.append(
                {
                    "name": doc.get("name", p.stem),
                    "updated_at": doc.get("updated_at", ""),
                    "count": len(doc.get("signatures", [])),
                    "path": str(p),
                }
            )
        except Exception:
            rows.append({"name": p.stem, "updated_at": "", "count": 0, "path": str(p)})
    return {"count": len(rows), "databases": rows}


def load_annotation_db(name: str) -> Dict[str, Any]:
    p = annotation_db_path(name)
    if not p.exists():
        raise ValueError("Annotation DB not found")
    return json.loads(p.read_text(encoding="utf-8"))


def annotate_with_db(record: SequenceRecord, db_name: str) -> Dict[str, Any]:
    doc = load_annotation_db(db_name)
    sigs = doc.get("signatures", [])
    rows = []
    circular = record.topology == "circular"
    for sig in sigs:
        motif = sanitize_sequence(str(sig.get("motif", "")))
        if not motif:
            continue
        for pos in find_all_occurrences(record.sequence, motif, circular=circular):
            start = pos + 1
            end = pos + len(motif)
            if end > record.length and circular:
                end -= record.length
            rows.append(
                {
                    "label": str(sig.get("label", motif)),
                    "type": str(sig.get("type", "misc_feature")),
                    "motif": motif,
                    "start_1based": start,
                    "end_1based": end,
                }
            )
    rows.sort(key=lambda x: x["start_1based"])
    return {"db_name": db_name, "count": len(rows), "annotations": rows}


def _pairwise_distance(a: str, b: str) -> float:
    aln = needleman_wunsch(a, b)
    return max(0.0, 100.0 - float(aln["identity_pct"]))


def phylo_upgma(sequences: List[str]) -> Dict[str, Any]:
    seqs = [parse_plain_sequence(s) for s in sequences if str(s).strip()]
    if len(seqs) < 2:
        raise ValueError("Need at least two sequences")
    clusters: Dict[int, Dict[str, Any]] = {i: {"members": [i], "label": f"S{i+1}"} for i in range(len(seqs))}
    dist: Dict[Tuple[int, int], float] = {}
    for i in range(len(seqs)):
        for j in range(i + 1, len(seqs)):
            dist[(i, j)] = _pairwise_distance(seqs[i], seqs[j])
    next_id = len(seqs)
    merges = []
    while len(clusters) > 1:
        ids = sorted(clusters.keys())
        best = None
        best_d = float("inf")
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                key = (a, b) if a < b else (b, a)
                d = dist.get(key, float("inf"))
                if d < best_d:
                    best_d = d
                    best = (a, b)
        if best is None:
            break
        a, b = best
        new_members = clusters[a]["members"] + clusters[b]["members"]
        new_label = f"({clusters[a]['label']}:{best_d/2:.2f},{clusters[b]['label']}:{best_d/2:.2f})"
        merges.append({"left": a, "right": b, "distance": round(best_d, 3), "new_id": next_id, "newick_partial": new_label})
        clusters[next_id] = {"members": new_members, "label": new_label}
        for k in list(clusters.keys()):
            if k in (a, b, next_id):
                continue
            # average linkage
            vals = []
            for x in clusters[k]["members"]:
                for y in new_members:
                    key = (x, y) if x < y else (y, x)
                    if key in dist:
                        vals.append(dist[key])
            if vals:
                key = (k, next_id) if k < next_id else (next_id, k)
                dist[key] = sum(vals) / len(vals)
        del clusters[a]
        del clusters[b]
        next_id += 1
    root = next(iter(clusters.values()))
    return {"sequence_count": len(seqs), "merges": merges, "newick": root["label"] + ";"}


GEL_MARKER_SETS: Dict[str, List[int]] = {
    "1kb_plus": [20000, 10000, 8000, 6000, 5000, 4000, 3000, 2000, 1500, 1000, 700, 500, 300, 100],
    "100bp": [3000, 2000, 1500, 1200, 1000, 900, 800, 700, 600, 500, 400, 300, 200, 100],
    "ultra_low": [1000, 900, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 75, 50, 25],
    "high_range": [50000, 40000, 30000, 20000, 15000, 10000, 8000, 6000, 5000, 4000, 3000, 2000, 1000],
}


def gel_simulate(fragment_sizes: List[int]) -> List[Dict[str, Any]]:
    # Approximate migration distance for agarose gel visualization.
    rows: List[Dict[str, Any]] = []
    if not fragment_sizes:
        return rows
    cleaned = sorted([max(1, int(x)) for x in fragment_sizes], reverse=True)
    if len(cleaned) == 1:
        return [{"size_bp": cleaned[0], "relative_migration": 0.5}]
    import math
    logs = [math.log10(x) for x in cleaned]
    lo = min(logs)
    hi = max(logs)
    span = max(1e-6, hi - lo)
    for size, lval in zip(cleaned, logs):
        size = max(1, int(size))
        # Larger fragments migrate less; map to 0.1..0.95
        norm = (lval - lo) / span
        dist = 0.95 - 0.85 * norm
        rows.append({"size_bp": size, "relative_migration": round(dist, 3)})
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
    for i, pair in enumerate(primer_pairs, start=1):
        fwd = str(pair.get("forward", "")).strip()
        rev = str(pair.get("reverse", "")).strip()
        if not fwd or not rev:
            lanes.append({"lane": i, "error": "forward/reverse required"})
            continue
        pcr = simulate_pcr(record, forward_primer=fwd, reverse_primer=rev)
        products = pcr.get("products", [])
        sizes = [int(x.get("size_bp", 0)) for x in products if int(x.get("size_bp", 0)) > 0]
        sample_sizes.extend(sizes)
        lanes.append(
            {
                "lane": i,
                "forward": fwd,
                "reverse": rev,
                "product_count": len(products),
                "product_sizes_bp": sizes,
                "bands": gel_simulate(sizes),
            }
        )
    out = gel_simulate_lanes(sample_sizes=sample_sizes, marker_set=marker_set)
    out["lanes"] = lanes
    return out


def _parse_feature_bounds(loc: str) -> Tuple[int, int]:
    nums = [int(x) for x in "".join(ch if ch.isdigit() else " " for ch in str(loc)).split()]
    if len(nums) < 2:
        return 0, 0
    a, b = nums[0], nums[-1]
    if a > b:
        a, b = b, a
    return a, b


def translated_feature_report(
    record: SequenceRecord,
    include_slippage: bool = False,
    slip_pos_1based: int = 0,
    slip_type: str = "-1",
) -> Dict[str, Any]:
    rows = []
    for idx, f in enumerate(record.features):
        if f.key.lower() != "cds":
            continue
        a, b = _parse_feature_bounds(f.location)
        if a <= 0 or b <= 0:
            continue
        region = record.sequence[a - 1 : b]
        codon_start = int(str(f.qualifiers.get("codon_start", "1")) or "1")
        codon_start = max(1, min(3, codon_start))
        seq = region[codon_start - 1 :]
        slippage_applied = None
        if include_slippage and slip_pos_1based >= a and slip_pos_1based <= b and seq:
            rel = slip_pos_1based - a
            if slip_type == "-1" and 0 <= rel < len(seq):
                seq = seq[:rel] + seq[rel + 1 :]
                slippage_applied = {"type": "-1", "position_1based": slip_pos_1based}
            elif slip_type == "+1" and 0 <= rel < len(seq):
                seq = seq[: rel + 1] + seq[rel] + seq[rel + 1 :]
                slippage_applied = {"type": "+1", "position_1based": slip_pos_1based}
        aa = []
        numbered = []
        for i in range(0, len(seq) - 2, 3):
            codon = seq[i : i + 3]
            residue = CODON_TABLE.get(codon, "X")
            aa.append(residue)
            numbered.append(
                {
                    "aa_index_1based": len(aa),
                    "codon": codon,
                    "residue": residue,
                    "genomic_codon_start_1based": a + codon_start - 1 + i,
                    "genomic_codon_end_1based": a + codon_start - 1 + i + 2,
                }
            )
        rows.append(
            {
                "feature_index": idx,
                "label": f.qualifiers.get("label") or f.qualifiers.get("gene") or f"CDS_{idx+1}",
                "location": f.location,
                "codon_start": codon_start,
                "translation_length_aa": len(aa),
                "translation": "".join(aa),
                "numbering": numbered,
                "slippage_applied": slippage_applied,
            }
        )
    return {"count": len(rows), "translated_features": rows}


def translated_feature_edit(
    record: SequenceRecord,
    feature_index: int,
    aa_index_1based: int,
    new_residue: str,
    host: str = "ecoli",
) -> Dict[str, Any]:
    if feature_index < 0 or feature_index >= len(record.features):
        raise ValueError("Invalid feature index")
    feat = record.features[feature_index]
    if feat.key.lower() != "cds":
        raise ValueError("Selected feature is not CDS")
    a, b = _parse_feature_bounds(feat.location)
    if a <= 0 or b <= 0:
        raise ValueError("Invalid CDS location")
    codon_start = int(str(feat.qualifiers.get("codon_start", "1")) or "1")
    codon_start = max(1, min(3, codon_start))
    cds_len = max(0, b - a + 1 - (codon_start - 1))
    aa_len = cds_len // 3
    if aa_index_1based < 1 or aa_index_1based > aa_len:
        raise ValueError("AA index out of range")
    res = str(new_residue).strip().upper()
    if len(res) != 1:
        raise ValueError("new_residue must be a single amino acid code")
    new_codon = reverse_translate_protein(res, host=host)[:3]
    codon_genomic_start = a + codon_start - 1 + (aa_index_1based - 1) * 3
    codon_genomic_end = codon_genomic_start + 2
    old_codon = record.sequence[codon_genomic_start - 1 : codon_genomic_end]
    edited = apply_sequence_edit(
        record,
        op="replace",
        start_1based=codon_genomic_start,
        end_1based=codon_genomic_end,
        value=new_codon,
    )
    return {
        "edited": True,
        "feature_index": feature_index,
        "aa_index_1based": aa_index_1based,
        "old_codon": old_codon,
        "new_codon": new_codon,
        "new_residue": res,
        "codon_genomic_start_1based": codon_genomic_start,
        "codon_genomic_end_1based": codon_genomic_end,
        "name": edited.name,
        "length": edited.length,
        "gc": round(edited.gc_content(), 2),
        "sequence": edited.sequence,
    }


def protein_edit_sequence(
    record: SequenceRecord,
    aa_index_1based: int,
    new_residue: str,
    frame: int = 1,
    host: str = "ecoli",
) -> Dict[str, Any]:
    if frame not in {1, 2, 3}:
        raise ValueError("frame must be 1,2,3")
    if aa_index_1based < 1:
        raise ValueError("aa_index_1based must be >= 1")
    res = str(new_residue).strip().upper()
    if len(res) != 1:
        raise ValueError("new_residue must be one amino acid letter")
    codon_start = frame + (aa_index_1based - 1) * 3
    codon_end = codon_start + 2
    if codon_end > record.length:
        raise ValueError("AA index exceeds translated range")
    old_codon = record.sequence[codon_start - 1 : codon_end]
    new_codon = reverse_translate_protein(res, host=host)[:3]
    edited = apply_sequence_edit(
        record,
        op="replace",
        start_1based=codon_start,
        end_1based=codon_end,
        value=new_codon,
    )
    return {
        "edited": True,
        "mode": "protein_edit",
        "frame": frame,
        "aa_index_1based": aa_index_1based,
        "old_codon": old_codon,
        "new_codon": new_codon,
        "new_residue": res,
        "codon_start_1based": codon_start,
        "codon_end_1based": codon_end,
        "name": edited.name,
        "sequence": edited.sequence,
        "length": edited.length,
        "gc": round(edited.gc_content(), 2),
    }


def search_entities(
    record: SequenceRecord,
    query: str,
    primers: List[str] | None = None,
) -> Dict[str, Any]:
    q = str(query or "").strip().upper()
    if not q:
        raise ValueError("query is required")
    seq = record.sequence
    motif_hits = find_all_occurrences(seq, q, circular=record.topology == "circular")
    motif_rows = [{"start_1based": p + 1, "end_1based": p + len(q)} for p in motif_hits]
    feat_rows = []
    for i, f in enumerate(record.features):
        label = (f.qualifiers.get("label") or f.qualifiers.get("gene") or f.key).upper()
        if q in label or q in f.key.upper() or q in f.location.upper():
            feat_rows.append({"feature_index": i, "key": f.key, "location": f.location, "label": label})
    primer_rows = []
    for idx, p in enumerate(primers or [], start=1):
        ps = sanitize_sequence(str(p))
        if not ps:
            continue
        starts = find_all_occurrences(seq, ps, circular=record.topology == "circular")
        if starts:
            primer_rows.append(
                {
                    "primer_index": idx,
                    "primer": ps,
                    "match_count": len(starts),
                    "positions_1based": [s + 1 for s in starts[:50]],
                }
            )
        elif q in ps:
            primer_rows.append({"primer_index": idx, "primer": ps, "match_count": 0, "positions_1based": []})
    return {
        "query": q,
        "motif_hit_count": len(motif_rows),
        "motif_hits": motif_rows,
        "feature_hit_count": len(feat_rows),
        "feature_hits": feat_rows,
        "primer_hit_count": len(primer_rows),
        "primer_hits": primer_rows,
    }


def cdna_to_genome_map(
    cdna_sequence: str,
    genome_sequence: str,
    min_exon_bp: int = 14,
    max_intron_bp: int = 200000,
) -> Dict[str, Any]:
    cdna = sanitize_sequence(cdna_sequence)
    genome = sanitize_sequence(genome_sequence)
    if not cdna or not genome:
        raise ValueError("cdna and genome sequences are required")
    i = 0
    g_cursor = 0
    exons: List[Dict[str, int]] = []
    while i < len(cdna):
        best = None
        max_len = min(len(cdna) - i, 300)
        for ln in range(max_len, min_exon_bp - 1, -1):
            frag = cdna[i : i + ln]
            search_start = g_cursor
            search_end = min(len(genome), g_cursor + max_intron_bp + ln)
            hit = genome.find(frag, search_start, search_end)
            if hit != -1:
                best = (hit, ln)
                break
        if not best:
            break
        hit, ln = best
        exons.append(
            {
                "cdna_start_1based": i + 1,
                "cdna_end_1based": i + ln,
                "genome_start_1based": hit + 1,
                "genome_end_1based": hit + ln,
                "length_bp": ln,
            }
        )
        i += ln
        g_cursor = hit + ln
    introns = []
    for k in range(len(exons) - 1):
        introns.append(
            {
                "from_exon": k + 1,
                "to_exon": k + 2,
                "genome_intron_start_1based": exons[k]["genome_end_1based"] + 1,
                "genome_intron_end_1based": exons[k + 1]["genome_start_1based"] - 1,
                "length_bp": max(0, exons[k + 1]["genome_start_1based"] - exons[k]["genome_end_1based"] - 1),
            }
        )
    aligned_bp = sum(e["length_bp"] for e in exons)
    return {
        "cdna_length": len(cdna),
        "genome_length": len(genome),
        "aligned_bp": aligned_bp,
        "coverage_pct": round(100.0 * aligned_bp / max(1, len(cdna)), 2),
        "exon_count": len(exons),
        "exons": exons,
        "introns": introns,
        "unmapped_cdna_tail_bp": max(0, len(cdna) - aligned_bp),
    }


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


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            self._send_html(INDEX_PATH.read_text(encoding="utf-8"))
            return
        if self.path.startswith("/share/"):
            share_id = self.path.split("/share/", 1)[1].strip().split("?", 1)[0].strip("/")
            if not share_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
                return
            try:
                self._send_html(render_share_view_html(share_id))
            except Exception as e:
                self.send_error(HTTPStatus.NOT_FOUND, str(e))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        try:
            n = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(n).decode("utf-8") if n > 0 else "{}")
            record: SequenceRecord | None = None

            def get_record() -> SequenceRecord:
                nonlocal record
                if record is None:
                    record = parse_record(payload)
                return record

            if self.path == "/api/canonicalize-record":
                rec = get_record()
                self._send_json(
                    {
                        "canonical_record": record_to_canonical(
                            rec,
                            source_format=infer_source_format(str(payload.get("content", ""))),
                            source_id=str(payload.get("record_id", "")).strip(),
                        )
                    }
                )
            elif self.path == "/api/convert-record":
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
                    self._send_json({"target_format": "fasta", "content": to_fasta(rec)})
                elif target == "genbank":
                    self._send_json({"target_format": "genbank", "content": to_genbank(rec)})
                elif target == "embl":
                    self._send_json({"target_format": "embl", "content": to_embl(rec)})
                elif target == "json":
                    self._send_json(
                        {
                            "target_format": "json",
                            "content": json.dumps(
                                {
                                    "payload": canonical_to_payload(canon),
                                    "canonical_record": canon,
                                },
                                indent=2,
                                sort_keys=True,
                            ),
                        }
                    )
                elif target in {"dna", "genomeforge_dna"}:
                    blob = export_dna_container(
                        canon,
                        metadata={
                            "name": rec.name,
                            "topology": rec.topology,
                            "created_by": "genomeforge",
                        },
                    )
                    self._send_json(
                        {
                            "target_format": "genomeforge_dna",
                            "dna_base64": _encode_b64(blob),
                            "bytes": len(blob),
                        }
                    )
                elif target == "payload":
                    self._send_json({"target_format": "payload", "payload": canonical_to_payload(canon)})
                elif target in {"canonical", "canonical_json"}:
                    self._send_json({"target_format": "canonical", "canonical_record": canon})
                else:
                    raise ValueError("Unsupported target_format. Use fasta|genbank|embl|json|dna|payload|canonical")
            elif self.path == "/api/import-dna":
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
                self._send_json(
                    {
                        "source": imported.get("source", "unknown"),
                        "name": rec.name,
                        "length": rec.length,
                        "topology": rec.topology,
                        "payload": doc_payload,
                        "canonical_record": canon,
                    }
                )
            elif self.path == "/api/export-dna":
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
                    metadata={
                        "name": rec.name,
                        "topology": rec.topology,
                        "created_by": "genomeforge",
                    },
                )
                self._send_json(
                    {
                        "format": "genomeforge.dna/1",
                        "name": rec.name,
                        "length": rec.length,
                        "dna_base64": _encode_b64(blob),
                        "bytes": len(blob),
                    }
                )
            elif self.path == "/api/import-ab1":
                if str(payload.get("ab1_base64", "")).strip():
                    raw = _decode_b64_field(str(payload.get("ab1_base64", "")).strip(), "ab1_base64")
                    tr = parse_ab1_bytes(raw)
                elif str(payload.get("sequence", "")).strip():
                    tr = synthetic_trace_from_sequence(str(payload.get("sequence", "")))
                else:
                    raise ValueError("ab1_base64 or sequence is required")
                tr = _cache_trace(tr)
                self._send_json({"trace_record": tr, "summary": trace_summary(tr)})
            elif self.path == "/api/trace-summary":
                tr = _resolve_trace(payload)
                tr = _cache_trace(tr)
                self._send_json({"trace_record": tr, "summary": trace_summary(tr)})
            elif self.path == "/api/trace-align":
                tr = _resolve_trace(payload)
                ref = str(payload.get("reference_sequence", payload.get("reference", "")))
                if not ref.strip():
                    raise ValueError("reference_sequence is required")
                out = align_trace_to_reference(tr, ref)
                tr = _cache_trace(tr)
                self._send_json({"trace_id": tr.get("trace_id"), **out})
            elif self.path == "/api/trace-edit-base":
                tr = _resolve_trace(payload)
                edited = edit_trace_base(
                    tr,
                    position_1based=int(payload.get("position_1based", 1)),
                    new_base=str(payload.get("new_base", "N")),
                    quality=(int(payload["quality"]) if "quality" in payload and payload.get("quality") is not None else None),
                )
                edited = _cache_trace(edited)
                self._send_json({"trace_record": edited, "summary": trace_summary(edited)})
            elif self.path == "/api/trace-consensus":
                tr = _resolve_trace(payload)
                tr = _cache_trace(tr)
                self._send_json(
                    {
                        "trace_id": tr.get("trace_id"),
                        **trace_consensus(tr, min_quality=int(payload.get("min_quality", 20))),
                    }
                )
            elif self.path == "/api/primer-specificity":
                backgrounds = payload.get("background_sequences", [])
                if isinstance(backgrounds, str):
                    backgrounds = [x.strip() for x in backgrounds.splitlines() if x.strip()]
                if not backgrounds:
                    rec = get_record()
                    backgrounds = [{"name": rec.name, "sequence": rec.sequence}]
                self._send_json(
                    primer_specificity_report(
                        forward=str(payload.get("forward", "")),
                        reverse=str(payload.get("reverse", "")),
                        background_sequences=backgrounds,
                        max_mismatch=int(payload.get("max_mismatch", 1)),
                        min_amplicon_bp=int(payload.get("min_amplicon_bp", 80)),
                        max_amplicon_bp=int(payload.get("max_amplicon_bp", 3000)),
                    )
                )
            elif self.path == "/api/primer-rank":
                backgrounds = payload.get("background_sequences", [])
                if isinstance(backgrounds, str):
                    backgrounds = [x.strip() for x in backgrounds.splitlines() if x.strip()]
                if not backgrounds:
                    rec = get_record()
                    backgrounds = [{"name": rec.name, "sequence": rec.sequence}]
                candidates = payload.get("candidates", [])
                if isinstance(candidates, str):
                    candidates = json.loads(candidates)
                self._send_json(
                    rank_primer_pairs(
                        candidates=[dict(x) for x in candidates if isinstance(x, dict)],
                        background_sequences=backgrounds,
                        max_mismatch=int(payload.get("max_mismatch", 1)),
                    )
                )
            elif self.path == "/api/grna-design":
                sequence = str(payload.get("sequence", ""))
                if not sequence.strip():
                    sequence = get_record().sequence
                self._send_json(
                    design_grna_candidates(
                        sequence=sequence,
                        pam=str(payload.get("pam", "NGG")),
                        spacer_len=int(payload.get("spacer_len", 20)),
                        max_candidates=int(payload.get("max_candidates", 200)),
                    )
                )
            elif self.path == "/api/crispr-offtarget":
                backgrounds = payload.get("background_sequences", [])
                if isinstance(backgrounds, str):
                    backgrounds = [x.strip() for x in backgrounds.splitlines() if x.strip()]
                if not backgrounds:
                    rec = get_record()
                    backgrounds = [{"name": rec.name, "sequence": rec.sequence}]
                self._send_json(
                    crispr_offtarget_scan(
                        guide=str(payload.get("guide", "")),
                        background_sequences=backgrounds,
                        max_mismatch=int(payload.get("max_mismatch", 3)),
                    )
                )
            elif self.path == "/api/hdr-template":
                sequence = str(payload.get("sequence", ""))
                if not sequence.strip():
                    sequence = get_record().sequence
                self._send_json(
                    design_hdr_template(
                        sequence=sequence,
                        edit_start_1based=int(payload.get("edit_start_1based", 1)),
                        edit_end_1based=int(payload.get("edit_end_1based", 1)),
                        edit_sequence=str(payload.get("edit_sequence", "")),
                        left_arm_bp=int(payload.get("left_arm_bp", 60)),
                        right_arm_bp=int(payload.get("right_arm_bp", 60)),
                    )
                )
            elif self.path == "/api/info":
                rec = get_record()
                self._send_json(
                    {
                        "name": rec.name,
                        "length": rec.length,
                        "topology": rec.topology,
                        "gc": round(rec.gc_content(), 2),
                        "features": len(rec.features),
                    }
                )
            elif self.path == "/api/translate":
                rec = get_record()
                frame = int(payload.get("frame", 1))
                to_stop = bool(payload.get("to_stop", False))
                self._send_json({"protein": rec.translate(frame=frame, to_stop=to_stop)})
            elif self.path == "/api/translated-features":
                rec = get_record()
                self._send_json(
                    translated_feature_report(
                        rec,
                        include_slippage=bool(payload.get("include_slippage", False)),
                        slip_pos_1based=int(payload.get("slip_pos_1based", 0)),
                        slip_type=str(payload.get("slip_type", "-1")),
                    )
                )
            elif self.path == "/api/digest":
                rec = get_record()
                enzymes = resolve_enzymes(payload)
                self._send_json(simulate_digest(rec, enzymes))
            elif self.path == "/api/digest-advanced":
                rec = get_record()
                enzymes = resolve_enzymes(payload)
                methylated = payload.get("methylated_motifs", [])
                if isinstance(methylated, str):
                    methylated = [x.strip() for x in methylated.split(",") if x.strip()]
                self._send_json(digest_with_methylation(rec, enzymes, methylated))
            elif self.path == "/api/star-activity-scan":
                rec = get_record()
                enzymes = resolve_enzymes(payload)
                self._send_json(
                    star_activity_scan(
                        rec,
                        enzymes=enzymes,
                        star_activity_level=float(payload.get("star_activity_level", 0.0)),
                        include_star_cuts=bool(payload.get("include_star_cuts", False)),
                    )
                )
            elif self.path == "/api/primers":
                rec = get_record()
                out = design_primer_pair(
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
                self._send_json(out)
            elif self.path == "/api/primer-diagnostics":
                self._send_json(
                    primer_diagnostics(
                        forward=str(payload.get("forward", "")),
                        reverse=str(payload.get("reverse", "")),
                        na_mM=float(payload.get("na_mM", 50.0)),
                        primer_nM=float(payload.get("primer_nM", 250.0)),
                    )
                )
            elif self.path == "/api/pcr":
                rec = get_record()
                self._send_json(
                    simulate_pcr(
                        rec,
                        forward_primer=payload["forward"],
                        reverse_primer=payload["reverse"],
                    )
                )
            elif self.path == "/api/codon-optimize":
                rec = get_record()
                out = optimize_coding_sequence(
                    rec.sequence,
                    host=str(payload.get("host", "ecoli")),
                    frame=int(payload.get("frame", 1)),
                    keep_stop=not bool(payload.get("drop_stop", False)),
                )
                self._send_json(out)
            elif self.path == "/api/map":
                rec = get_record()
                enzymes = payload.get("enzymes", [])
                if isinstance(enzymes, str):
                    enzymes = [x.strip() for x in enzymes.split(",") if x.strip()]
                self._send_json({"svg": build_svg_map(rec, enzyme_names=enzymes)})
            elif self.path == "/api/sequence-tracks":
                rec = get_record()
                self._send_json(
                    sequence_track_svg(
                        rec,
                        start_1based=int(payload.get("start", 1)),
                        end_1based=int(payload.get("end", min(rec.length, 300))),
                        frame=int(payload.get("frame", 1)),
                    )
                )
            elif self.path == "/api/sequence-analytics-svg":
                rec = get_record()
                self._send_json(
                    sequence_analytics_svg(
                        rec,
                        start_1based=int(payload.get("start", 1)),
                        end_1based=int(payload.get("end", rec.length)),
                        window=int(payload.get("window", 120)),
                        step=int(payload.get("step", 20)),
                    )
                )
            elif self.path == "/api/orfs":
                rec = get_record()
                min_aa = int(payload.get("min_aa", 50))
                orfs = rec.find_orfs(min_aa_len=min_aa)
                rows = [
                    {
                        "start": start,
                        "end": end,
                        "frame": frame,
                        "aa_len": len(protein),
                        "protein_preview": protein[:40],
                    }
                    for start, end, frame, protein in orfs
                ]
                self._send_json({"count": len(rows), "orfs": rows})
            elif self.path == "/api/annotate-auto":
                rec = get_record()
                self._send_json(auto_annotate(rec))
            elif self.path == "/api/annot-db-save":
                name = str(payload.get("db_name", "")).strip()
                sigs = payload.get("signatures", [])
                if isinstance(sigs, str):
                    sigs = json.loads(sigs)
                self._send_json(save_annotation_db(name, sigs))
            elif self.path == "/api/annot-db-list":
                self._send_json(list_annotation_dbs())
            elif self.path == "/api/annot-db-load":
                self._send_json(load_annotation_db(str(payload.get("db_name", "")).strip()))
            elif self.path == "/api/annot-db-apply":
                rec = get_record()
                self._send_json(annotate_with_db(rec, str(payload.get("db_name", "")).strip()))
            elif self.path == "/api/features-list":
                rec = get_record()
                self._send_json({"count": len(rec.features), "features": features_to_dict(rec.features)})
            elif self.path == "/api/features-add":
                rec = get_record()
                key = str(payload.get("key", "misc_feature"))
                location = str(payload.get("location", ""))
                qualifiers = payload.get("qualifiers", {})
                if isinstance(qualifiers, dict):
                    q = {str(k): str(v) for k, v in qualifiers.items()}
                else:
                    q = {}
                rec.features.append(Feature(key=key, location=location, qualifiers=q))
                self._send_json({"count": len(rec.features), "features": features_to_dict(rec.features)})
            elif self.path == "/api/features-update":
                rec = get_record()
                idx = int(payload.get("index", -1))
                if idx < 0 or idx >= len(rec.features):
                    raise ValueError("feature index out of range")
                f = rec.features[idx]
                if "key" in payload:
                    f.key = str(payload.get("key"))
                if "location" in payload:
                    f.location = str(payload.get("location"))
                if "qualifiers" in payload and isinstance(payload.get("qualifiers"), dict):
                    f.qualifiers = {str(k): str(v) for k, v in payload["qualifiers"].items()}
                self._send_json({"count": len(rec.features), "features": features_to_dict(rec.features)})
            elif self.path == "/api/features-delete":
                rec = get_record()
                idx = int(payload.get("index", -1))
                if idx < 0 or idx >= len(rec.features):
                    raise ValueError("feature index out of range")
                del rec.features[idx]
                self._send_json({"count": len(rec.features), "features": features_to_dict(rec.features)})
            elif self.path == "/api/motif":
                rec = get_record()
                motif = sanitize_sequence(str(payload.get("motif", "")))
                if not motif:
                    raise ValueError("motif is required")
                positions = find_all_occurrences(
                    rec.sequence,
                    motif,
                    circular=rec.topology == "circular",
                )
                self._send_json(
                    {
                        "motif": motif,
                        "count": len(positions),
                        "positions_1based": [p + 1 for p in positions],
                    }
                )
            elif self.path == "/api/enzyme-scan":
                rec = get_record()
                names = resolve_enzymes(payload)
                if not names:
                    names = sorted(ENZYMES.keys())
                hits = []
                for name in names:
                    site, _ = ENZYMES[name]
                    positions = find_all_occurrences(
                        rec.sequence,
                        site,
                        circular=rec.topology == "circular",
                    )
                    if positions:
                        hits.append(
                            {
                                "enzyme": name,
                                "site": site,
                                "count": len(positions),
                                "positions_1based": [p + 1 for p in positions[:20]],
                            }
                        )
                self._send_json({"hit_count": len(hits), "enzymes": hits})
            elif self.path == "/api/enzyme-info":
                names = resolve_enzymes(payload)
                if not names:
                    names = sorted(ENZYME_META.keys())
                rows = []
                for name in names:
                    if name in ENZYME_META:
                        rows.append({"enzyme": name, **ENZYME_META[name]})
                self._send_json({"count": len(rows), "enzymes": rows})
            elif self.path == "/api/enzyme-set-save":
                name = str(payload.get("set_name", "")).strip()
                enzymes = payload.get("enzymes", [])
                if isinstance(enzymes, str):
                    enzymes = [x.strip() for x in enzymes.split(",") if x.strip()]
                self._send_json(save_enzyme_set(name, [str(x) for x in enzymes], notes=str(payload.get("notes", ""))))
            elif self.path == "/api/enzyme-set-list":
                self._send_json(list_enzyme_sets())
            elif self.path == "/api/enzyme-set-predefined":
                self._send_json(list_predefined_enzyme_sets())
            elif self.path == "/api/enzyme-set-load":
                self._send_json(load_enzyme_set(str(payload.get("set_name", "")).strip()))
            elif self.path == "/api/enzyme-set-delete":
                self._send_json(delete_enzyme_set(str(payload.get("set_name", "")).strip()))
            elif self.path == "/api/sequence-edit":
                rec = get_record()
                edited = apply_sequence_edit(
                    rec,
                    op=str(payload.get("op", "")).lower(),
                    start_1based=int(payload.get("start", 1)),
                    end_1based=int(payload.get("end", 0)),
                    value=str(payload.get("value", "")),
                )
                self._send_json(
                    {
                        "name": edited.name,
                        "length": edited.length,
                        "topology": edited.topology,
                        "gc": round(edited.gc_content(), 2),
                        "sequence": edited.sequence,
                    }
                )
            elif self.path == "/api/reverse-translate":
                protein = str(payload.get("protein", "")).strip().upper()
                host = str(payload.get("host", "ecoli")).lower()
                dna = reverse_translate_protein(protein, host=host)
                self._send_json({"protein": protein, "host": host, "dna": dna, "length": len(dna)})
            elif self.path == "/api/pairwise-align":
                seq_a = str(payload.get("seq_a", ""))
                seq_b = str(payload.get("seq_b", ""))
                mode = str(payload.get("mode", "dna")).lower()
                if mode == "protein":
                    self._send_json(needleman_wunsch_protein(seq_a, seq_b))
                else:
                    out = needleman_wunsch(seq_a, seq_b)
                    out["mode"] = "dna"
                    self._send_json(out)
            elif self.path == "/api/comparison-lens-svg":
                seq_a = str(payload.get("seq_a", ""))
                seq_b = str(payload.get("seq_b", ""))
                if not seq_a.strip():
                    seq_a = get_record().sequence
                self._send_json(
                    comparison_lens_svg(
                        seq_a=seq_a,
                        seq_b=seq_b,
                        window=int(payload.get("window", 60)),
                    )
                )
            elif self.path == "/api/multi-align":
                sequences = payload.get("sequences", [])
                if isinstance(sequences, str):
                    sequences = [x.strip() for x in sequences.splitlines() if x.strip()]
                self._send_json(multi_align_to_reference([str(x) for x in sequences]))
            elif self.path == "/api/contig-assemble":
                reads = payload.get("reads", [])
                if isinstance(reads, str):
                    reads = [x.strip() for x in reads.splitlines() if x.strip()]
                self._send_json(contig_assemble([str(x) for x in reads], min_overlap=int(payload.get("min_overlap", 20))))
            elif self.path == "/api/msa":
                sequences = payload.get("sequences", [])
                if isinstance(sequences, str):
                    sequences = [x.strip() for x in sequences.splitlines() if x.strip()]
                method = str(payload.get("method", "progressive")).lower()
                if method == "progressive":
                    self._send_json(progressive_msa([str(x) for x in sequences]))
                else:
                    self._send_json(external_msa(method, [str(x) for x in sequences]))
            elif self.path == "/api/alignment-consensus":
                alignment = payload.get("alignment", [])
                if isinstance(alignment, str):
                    alignment = [x.strip() for x in alignment.splitlines() if x.strip()]
                self._send_json(alignment_consensus([str(x) for x in alignment]))
            elif self.path == "/api/alignment-heatmap-svg":
                alignment = payload.get("alignment", [])
                if isinstance(alignment, str):
                    alignment = [x.strip() for x in alignment.splitlines() if x.strip()]
                self._send_json(alignment_heatmap_svg([str(x) for x in alignment]))
            elif self.path == "/api/phylo-tree":
                sequences = payload.get("sequences", [])
                if isinstance(sequences, str):
                    sequences = [x.strip() for x in sequences.splitlines() if x.strip()]
                self._send_json(phylo_upgma([str(x) for x in sequences]))
            elif self.path == "/api/anneal-oligos":
                forward = str(payload.get("forward", ""))
                reverse = str(payload.get("reverse", ""))
                min_overlap = int(payload.get("min_overlap", 10))
                self._send_json(anneal_oligos(forward, reverse, min_overlap=min_overlap))
            elif self.path == "/api/mutagenesis":
                rec = get_record()
                start = int(payload.get("start", 1))
                end = int(payload.get("end", start))
                mutant = sanitize_sequence(str(payload.get("mutant", "")))
                edited = apply_sequence_edit(rec, op="replace", start_1based=start, end_1based=end, value=mutant)
                self._send_json(
                    {
                        "start": start,
                        "end": end,
                        "mutant": mutant,
                        "length": edited.length,
                        "gc": round(edited.gc_content(), 2),
                        "sequence": edited.sequence,
                    }
                )
            elif self.path == "/api/protein-edit":
                rec = get_record()
                self._send_json(
                    protein_edit_sequence(
                        rec,
                        aa_index_1based=int(payload.get("aa_index_1based", 1)),
                        new_residue=str(payload.get("new_residue", "A")),
                        frame=int(payload.get("frame", 1)),
                        host=str(payload.get("host", "ecoli")),
                    )
                )
            elif self.path == "/api/translated-feature-edit":
                rec = get_record()
                self._send_json(
                    translated_feature_edit(
                        rec,
                        feature_index=int(payload.get("feature_index", 0)),
                        aa_index_1based=int(payload.get("aa_index_1based", 1)),
                        new_residue=str(payload.get("new_residue", "A")),
                        host=str(payload.get("host", "ecoli")),
                    )
                )
            elif self.path == "/api/gel-sim":
                sizes = payload.get("sizes", [])
                if isinstance(sizes, str):
                    sizes = [int(x.strip()) for x in sizes.split(",") if x.strip()]
                marker_set = str(payload.get("marker_set", "1kb_plus")).strip() or "1kb_plus"
                self._send_json(gel_simulate_lanes([int(x) for x in sizes], marker_set=marker_set))
            elif self.path == "/api/gel-marker-sets":
                self._send_json({"marker_sets": GEL_MARKER_SETS, "count": len(GEL_MARKER_SETS)})
            elif self.path == "/api/pcr-gel-lanes":
                rec = get_record()
                pairs = payload.get("primer_pairs", [])
                if isinstance(pairs, dict):
                    pairs = [pairs]
                self._send_json(
                    pcr_gel_lanes(
                        rec,
                        primer_pairs=[dict(x) for x in pairs if isinstance(x, dict)],
                        marker_set=str(payload.get("marker_set", "1kb_plus")),
                    )
                )
            elif self.path == "/api/cdna-map":
                self._send_json(
                    cdna_to_genome_map(
                        cdna_sequence=str(payload.get("cdna_sequence", "")),
                        genome_sequence=str(payload.get("genome_sequence", "")),
                        min_exon_bp=int(payload.get("min_exon_bp", 14)),
                        max_intron_bp=int(payload.get("max_intron_bp", 200000)),
                    )
                )
            elif self.path == "/api/batch-digest":
                records = payload.get("records", [])
                enzymes = payload.get("enzymes", [])
                if isinstance(enzymes, str):
                    enzymes = [x.strip() for x in enzymes.split(",") if x.strip()]
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
                self._send_json({"count": len(out_rows), "results": out_rows})
            elif self.path == "/api/search-entities":
                rec = get_record()
                primers = payload.get("primers", [])
                if isinstance(primers, str):
                    primers = [x.strip() for x in primers.split(",") if x.strip()]
                self._send_json(
                    search_entities(
                        rec,
                        query=str(payload.get("query", "")),
                        primers=[str(x) for x in primers],
                    )
                )
            elif self.path == "/api/workspace-create":
                members = payload.get("members", [])
                if isinstance(members, str):
                    members = [x.strip() for x in members.split(",") if x.strip()]
                self._send_json(
                    create_workspace(
                        COLLAB_ROOT,
                        workspace_name=str(payload.get("workspace_name", "")).strip(),
                        owner=str(payload.get("owner", "")).strip(),
                        members=[str(x) for x in members],
                    )
                )
            elif self.path == "/api/project-permissions":
                project_name = str(payload.get("project_name", "")).strip()
                if not project_name:
                    raise ValueError("project_name is required")
                if isinstance(payload.get("roles"), dict):
                    self._send_json(
                        set_project_permissions(
                            COLLAB_ROOT,
                            project_name=project_name,
                            roles={str(k): str(v) for k, v in dict(payload.get("roles", {})).items()},
                        )
                    )
                else:
                    self._send_json(get_project_permissions(COLLAB_ROOT, project_name))
            elif self.path == "/api/project-audit-log":
                project_name = str(payload.get("project_name", "")).strip()
                if not project_name:
                    raise ValueError("project_name is required")
                if str(payload.get("action", "")).strip():
                    evt = append_audit_event(
                        COLLAB_ROOT,
                        project_name=project_name,
                        action=str(payload.get("action", "")),
                        actor=str(payload.get("actor", "system")),
                        details=dict(payload.get("details", {})) if isinstance(payload.get("details"), dict) else {},
                    )
                    self._send_json({"logged": True, "event": evt})
                else:
                    self._send_json(get_audit_log(COLLAB_ROOT, project_name, limit=int(payload.get("limit", 200))))
            elif self.path == "/api/project-diff":
                if str(payload.get("project_name_a", "")).strip() and str(payload.get("project_name_b", "")).strip():
                    a = load_project(str(payload.get("project_name_a", "")).strip())
                    b = load_project(str(payload.get("project_name_b", "")).strip())
                elif isinstance(payload.get("project_a"), dict) and isinstance(payload.get("project_b"), dict):
                    a = payload["project_a"]
                    b = payload["project_b"]
                else:
                    raise ValueError("Provide project_name_a/project_name_b or project_a/project_b")
                self._send_json(diff_projects(a, b))
            elif self.path == "/api/review-submit":
                project_name = str(payload.get("project_name", "")).strip()
                if not project_name:
                    raise ValueError("project_name is required")
                snapshot = load_project(project_name)
                out = submit_review(
                    COLLAB_ROOT,
                    project_name=project_name,
                    submitter=str(payload.get("submitter", "")).strip(),
                    summary=str(payload.get("summary", "")),
                    project_snapshot=snapshot,
                )
                append_audit_event(
                    COLLAB_ROOT,
                    project_name=project_name,
                    action="review_submit",
                    actor=str(payload.get("submitter", "system")),
                    details={"review_id": out["review"]["review_id"]},
                )
                self._send_json(out)
            elif self.path == "/api/review-approve":
                review_id = str(payload.get("review_id", "")).strip()
                reviewer = str(payload.get("reviewer", "")).strip()
                if not review_id or not reviewer:
                    raise ValueError("review_id and reviewer are required")
                project_name = str(payload.get("project_name", "")).strip()
                if project_name:
                    role = role_for_user(COLLAB_ROOT, project_name, reviewer)
                    if role not in {"reviewer", "owner"}:
                        raise ValueError("reviewer lacks permission (requires reviewer|owner role)")
                out = approve_review(
                    COLLAB_ROOT,
                    review_id=review_id,
                    reviewer=reviewer,
                    note=str(payload.get("note", "")),
                )
                proj = project_name or str(out.get("review", {}).get("project_name", "")).strip()
                if proj:
                    append_audit_event(
                        COLLAB_ROOT,
                        project_name=proj,
                        action="review_approve",
                        actor=reviewer,
                        details={"review_id": review_id},
                    )
                self._send_json(out)
            elif self.path == "/api/project-save":
                self._send_json(save_project(payload))
            elif self.path == "/api/project-load":
                self._send_json(load_project(str(payload.get("project_name", "")).strip()))
            elif self.path == "/api/project-list":
                self._send_json(list_projects())
            elif self.path == "/api/project-delete":
                self._send_json(delete_project(str(payload.get("project_name", "")).strip()))
            elif self.path == "/api/collection-save":
                projects = payload.get("projects", [])
                if isinstance(projects, str):
                    projects = [x.strip() for x in projects.split(",") if x.strip()]
                self._send_json(
                    save_collection(
                        str(payload.get("collection_name", "")).strip(),
                        [str(x) for x in projects],
                        notes=str(payload.get("notes", "")),
                    )
                )
            elif self.path == "/api/collection-load":
                self._send_json(load_collection(str(payload.get("collection_name", "")).strip()))
            elif self.path == "/api/collection-list":
                self._send_json(list_collections())
            elif self.path == "/api/collection-delete":
                self._send_json(delete_collection(str(payload.get("collection_name", "")).strip()))
            elif self.path == "/api/collection-add-project":
                self._send_json(
                    add_project_to_collection(
                        str(payload.get("collection_name", "")).strip(),
                        str(payload.get("project_name", "")).strip(),
                    )
                )
            elif self.path == "/api/share-create":
                projects = payload.get("projects", [])
                if isinstance(projects, str):
                    projects = [x.strip() for x in projects.split(",") if x.strip()]
                self._send_json(
                    create_share_bundle(
                        [str(x) for x in projects],
                        collection_name=str(payload.get("collection_name", "")).strip(),
                        include_content=bool(payload.get("include_content", True)),
                    )
                )
            elif self.path == "/api/share-load":
                self._send_json(load_share_bundle(str(payload.get("share_id", "")).strip()))
            elif self.path == "/api/project-history-graph":
                self._send_json(project_history_graph(str(payload.get("project_name", "")).strip()))
            elif self.path == "/api/project-history-svg":
                self._send_json(project_history_svg(str(payload.get("project_name", "")).strip()))
            elif self.path == "/api/gibson-assemble":
                fragments = payload.get("fragments", [])
                min_overlap = int(payload.get("min_overlap", 20))
                circular = bool(payload.get("circular", False))
                self._send_json(gibson_assemble([str(x) for x in fragments], min_overlap=min_overlap, circular=circular))
            elif self.path == "/api/golden-gate":
                parts = payload.get("parts", [])
                circular = bool(payload.get("circular", True))
                enforce_complement = bool(payload.get("enforce_complement", True))
                self._send_json(golden_gate_assemble(parts, circular=circular, enforce_complement=enforce_complement))
            elif self.path == "/api/gateway-cloning":
                self._send_json(
                    gateway_cloning(
                        entry_clone=str(payload.get("entry_clone", "")),
                        destination_vector=str(payload.get("destination_vector", "")),
                        attl=str(payload.get("attl", "ACAAGTTTGTACAAAAAAGCAGGCT")),
                        attr=str(payload.get("attr", "ACCACTTTGTACAAGAAAGCTGGGT")),
                    )
                )
            elif self.path == "/api/topo-cloning":
                self._send_json(
                    topo_cloning(
                        vector=str(payload.get("vector", "")),
                        insert=str(payload.get("insert", "")),
                        mode=str(payload.get("mode", "TA")),
                    )
                )
            elif self.path == "/api/ta-gc-cloning":
                self._send_json(
                    ta_gc_cloning(
                        vector=str(payload.get("vector", "")),
                        insert=str(payload.get("insert", "")),
                        mode=str(payload.get("mode", "TA")),
                    )
                )
            elif self.path == "/api/cloning-compatibility":
                enzymes = payload.get("enzymes", [])
                if isinstance(enzymes, str):
                    enzymes = [x.strip() for x in enzymes.split(",") if x.strip()]
                self._send_json(
                    cloning_compatibility_check(
                        mode=str(payload.get("mode", "restriction")),
                        vector=str(payload.get("vector", "")),
                        insert=str(payload.get("insert", "")),
                        enzymes=[str(x) for x in enzymes],
                        left_overhang=str(payload.get("left_overhang", "")),
                        right_overhang=str(payload.get("right_overhang", "")),
                        min_overlap=int(payload.get("min_overlap", 15)),
                    )
                )
            elif self.path == "/api/ligation-sim":
                self._send_json(
                    ligation_simulate(
                        vector_sequence=str(payload.get("vector_sequence", "")),
                        insert_sequence=str(payload.get("insert_sequence", "")),
                        vector_left_enzyme=str(payload.get("vector_left_enzyme", "")),
                        vector_right_enzyme=str(payload.get("vector_right_enzyme", "")),
                        insert_left_enzyme=str(payload.get("insert_left_enzyme", "")),
                        insert_right_enzyme=str(payload.get("insert_right_enzyme", "")),
                        derive_from_sequence=bool(payload.get("derive_from_sequence", False)),
                        include_byproducts=bool(payload.get("include_byproducts", True)),
                        temp_c=float(payload.get("temp_c", 16.0)),
                        ligase_units=float(payload.get("ligase_units", 1.0)),
                        vector_insert_ratio=float(payload.get("vector_insert_ratio", 1.0)),
                        dna_ng=float(payload.get("dna_ng", 100.0)),
                        phosphatase_treated_vector=bool(payload.get("phosphatase_treated_vector", False)),
                        star_activity_level=float(payload.get("star_activity_level", 0.0)),
                    )
                )
            elif self.path == "/api/in-fusion":
                fragments = payload.get("fragments", [])
                self._send_json(
                    in_fusion_assemble(
                        fragments=[str(x) for x in fragments],
                        min_overlap=int(payload.get("min_overlap", 15)),
                        circular=bool(payload.get("circular", False)),
                    )
                )
            elif self.path == "/api/overlap-extension-pcr":
                self._send_json(
                    overlap_extension_pcr(
                        fragment_a=str(payload.get("fragment_a", "")),
                        fragment_b=str(payload.get("fragment_b", "")),
                        min_overlap=int(payload.get("min_overlap", 18)),
                    )
                )
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except Exception as e:  # pragma: no cover - user-facing service
            self._send_json({"error": str(e)}, status=400)


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Genome Forge web UI running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run Genome Forge local web UI")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    run(host=args.host, port=args.port)
