from __future__ import annotations

from typing import Any, Dict, List


def _clean(seq: str) -> str:
    return "".join(ch for ch in str(seq).upper() if ch in "ACGTN")


def _revcomp(seq: str) -> str:
    return _clean(seq).translate(str.maketrans("ACGTN", "TGCAN"))[::-1]


def _hamming(a: str, b: str) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)


def _pam_match(window: str, pam: str) -> bool:
    if len(window) != len(pam):
        return False
    for a, b in zip(window, pam):
        if b == "N":
            continue
        if a != b:
            return False
    return True


def _efficiency_score(spacer: str) -> float:
    s = _clean(spacer)
    if not s:
        return 0.0
    gc = (s.count("G") + s.count("C")) / len(s)
    gc_term = max(0.0, 1.0 - abs(gc - 0.5) / 0.5)  # peak near 50%
    poly_t_penalty = 0.25 if "TTTT" in s else 0.0
    score = (0.65 * gc_term + 0.35) - poly_t_penalty
    return round(max(0.0, min(1.0, score)) * 100, 2)


def _normalize_backgrounds(background_sequences: List[Any]) -> List[Dict[str, str]]:
    out = []
    for i, item in enumerate(background_sequences or []):
        if isinstance(item, dict):
            name = str(item.get("name", f"bg_{i+1}")).strip() or f"bg_{i+1}"
            seq = _clean(str(item.get("sequence", "")))
        else:
            name = f"bg_{i+1}"
            seq = _clean(str(item))
        if seq:
            out.append({"name": name, "sequence": seq})
    return out


def design_grna_candidates(
    sequence: str,
    pam: str = "NGG",
    spacer_len: int = 20,
    max_candidates: int = 200,
) -> Dict[str, Any]:
    seq = _clean(sequence)
    pam = _clean(pam)
    if len(seq) < spacer_len + len(pam):
        raise ValueError("sequence too short for spacer+PAM")
    if not pam or len(pam) != 3:
        raise ValueError("pam must be 3 bases (e.g., NGG)")

    rows = []
    Lp = len(pam)
    # plus-strand (spacer then PAM)
    for i in range(0, len(seq) - spacer_len - Lp + 1):
        spacer = seq[i : i + spacer_len]
        p = seq[i + spacer_len : i + spacer_len + Lp]
        if _pam_match(p, pam):
            rows.append(
                {
                    "guide": spacer,
                    "pam": p,
                    "strand": "+",
                    "start_1based": i + 1,
                    "end_1based": i + spacer_len,
                    "cut_site_1based": i + spacer_len - 3,
                    "gc_pct": round((spacer.count("G") + spacer.count("C")) / spacer_len * 100, 2),
                    "efficiency_score": _efficiency_score(spacer),
                }
            )
    # minus-strand (reverse-complement model)
    rc_pam = _revcomp(pam)
    for i in range(0, len(seq) - Lp - spacer_len + 1):
        p = seq[i : i + Lp]
        if not _pam_match(p, rc_pam):
            continue
        protospacer_plus = seq[i + Lp : i + Lp + spacer_len]
        if len(protospacer_plus) < spacer_len:
            continue
        spacer = _revcomp(protospacer_plus)
        rows.append(
            {
                "guide": spacer,
                "pam": p,
                "strand": "-",
                "start_1based": i + Lp + 1,
                "end_1based": i + Lp + spacer_len,
                "cut_site_1based": i + Lp + 3,
                "gc_pct": round((spacer.count("G") + spacer.count("C")) / spacer_len * 100, 2),
                "efficiency_score": _efficiency_score(spacer),
            }
        )
    rows.sort(key=lambda x: (-x["efficiency_score"], abs(x["gc_pct"] - 50.0), x["start_1based"]))
    rows = rows[: max(1, int(max_candidates))]
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return {"count": len(rows), "pam": pam, "spacer_len": spacer_len, "candidates": rows}


def crispr_offtarget_scan(
    guide: str,
    background_sequences: List[Any],
    max_mismatch: int = 3,
) -> Dict[str, Any]:
    g = _clean(guide)
    if len(g) < 17:
        raise ValueError("guide must be at least 17 nt")
    bgs = _normalize_backgrounds(background_sequences)
    if not bgs:
        raise ValueError("background_sequences is required")
    hits = []
    for bg in bgs:
        s = bg["sequence"]
        if len(s) < len(g):
            continue
        for i in range(len(s) - len(g) + 1):
            w = s[i : i + len(g)]
            mm = _hamming(w, g)
            if mm <= max_mismatch:
                hits.append(
                    {
                        "background": bg["name"],
                        "start_1based": i + 1,
                        "end_1based": i + len(g),
                        "mismatches": mm,
                        "match_sequence": w,
                        "is_exact": mm == 0,
                    }
                )
    hits.sort(key=lambda x: (x["mismatches"], x["background"], x["start_1based"]))
    counts = {str(i): 0 for i in range(max_mismatch + 1)}
    for h in hits:
        counts[str(h["mismatches"])] += 1
    risk = min(100.0, round(counts.get("0", 0) * 30 + counts.get("1", 0) * 12 + counts.get("2", 0) * 5 + counts.get("3", 0) * 2, 2))
    return {
        "guide": g,
        "background_count": len(bgs),
        "max_mismatch": max_mismatch,
        "hit_count": len(hits),
        "counts_by_mismatch": counts,
        "offtarget_risk_score": risk,
        "hits": hits[:500],
    }


def design_hdr_template(
    sequence: str,
    edit_start_1based: int,
    edit_end_1based: int,
    edit_sequence: str,
    left_arm_bp: int = 60,
    right_arm_bp: int = 60,
) -> Dict[str, Any]:
    seq = _clean(sequence)
    edit = _clean(edit_sequence)
    if not seq:
        raise ValueError("sequence is required")
    if edit_start_1based < 1 or edit_end_1based < edit_start_1based or edit_end_1based > len(seq):
        raise ValueError("invalid edit coordinates")
    ls = max(0, (edit_start_1based - 1) - left_arm_bp)
    le = edit_start_1based - 1
    rs = edit_end_1based
    re = min(len(seq), edit_end_1based + right_arm_bp)
    left = seq[ls:le]
    right = seq[rs:re]
    donor = left + edit + right
    edited_locus = seq[: edit_start_1based - 1] + edit + seq[edit_end_1based :]
    suggested_disrupt = []
    window_start = max(0, edit_start_1based - 15)
    window_end = min(len(edited_locus), edit_start_1based + len(edit) + 15)
    window = edited_locus[window_start:window_end]
    for i in range(max(0, len(window) - 2)):
        tri = window[i : i + 3]
        if tri.endswith("GG"):
            suggested_disrupt.append(
                {
                    "pam_seq": tri,
                    "pam_start_1based": window_start + i + 1,
                    "suggestion": "Consider silent mutation in PAM/protospacer to reduce re-cut risk",
                }
            )
            if len(suggested_disrupt) >= 5:
                break
    return {
        "edit_start_1based": edit_start_1based,
        "edit_end_1based": edit_end_1based,
        "left_arm_bp": len(left),
        "right_arm_bp": len(right),
        "edit_length": len(edit),
        "donor_length": len(donor),
        "donor_sequence": donor,
        "edited_locus_preview": edited_locus[max(0, edit_start_1based - 30) : min(len(edited_locus), edit_start_1based + len(edit) + 30)],
        "pam_disruption_suggestions": suggested_disrupt,
    }

