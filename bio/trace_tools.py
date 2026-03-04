from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _clean_dna(s: str) -> str:
    return "".join(ch for ch in str(s).upper() if ch in "ACGTN")


def needleman_wunsch_simple(a: str, b: str, match: int = 2, mismatch: int = -1, gap: int = -2) -> Dict[str, Any]:
    x = _clean_dna(a)
    y = _clean_dna(b)
    n, m = len(x), len(y)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    bt = [[0] * (m + 1) for _ in range(n + 1)]  # 1=diag,2=up,3=left
    for i in range(1, n + 1):
        dp[i][0] = i * gap
        bt[i][0] = 2
    for j in range(1, m + 1):
        dp[0][j] = j * gap
        bt[0][j] = 3
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = match if x[i - 1] == y[j - 1] else mismatch
            cand = [(dp[i - 1][j - 1] + s, 1), (dp[i - 1][j] + gap, 2), (dp[i][j - 1] + gap, 3)]
            dp[i][j], bt[i][j] = max(cand, key=lambda t: t[0])
    i, j = n, m
    aa: List[str] = []
    bb: List[str] = []
    while i > 0 or j > 0:
        step = bt[i][j] if i >= 0 and j >= 0 else 0
        if step == 1:
            aa.append(x[i - 1])
            bb.append(y[j - 1])
            i -= 1
            j -= 1
        elif step == 2:
            aa.append(x[i - 1])
            bb.append("-")
            i -= 1
        else:
            aa.append("-")
            bb.append(y[j - 1])
            j -= 1
    aligned_a = "".join(reversed(aa))
    aligned_b = "".join(reversed(bb))
    matches = sum(1 for p, q in zip(aligned_a, aligned_b) if p == q and p != "-")
    aligned_bases = sum(1 for p, q in zip(aligned_a, aligned_b) if p != "-" and q != "-")
    ident = round((matches / aligned_bases) * 100, 2) if aligned_bases else 0.0
    return {"aligned_a": aligned_a, "aligned_b": aligned_b, "score": dp[n][m], "identity_pct": ident}


def trace_summary(trace_record: Dict[str, Any]) -> Dict[str, Any]:
    seq = _clean_dna(trace_record.get("sequence", ""))
    quality = [int(x) for x in trace_record.get("quality", []) if isinstance(x, (int, float))]
    if not quality:
        quality = [30] * len(seq)
    q_mean = round(sum(quality) / len(quality), 2) if quality else 0.0
    q_min = min(quality) if quality else 0
    q_max = max(quality) if quality else 0
    low_q = sum(1 for q in quality if q < 20)
    return {
        "trace_id": str(trace_record.get("trace_id", "")),
        "source": str(trace_record.get("source", "unknown")),
        "length": len(seq),
        "sequence_preview": seq[:80],
        "base_order": str(trace_record.get("base_order", "GATC")),
        "quality_mean": q_mean,
        "quality_min": q_min,
        "quality_max": q_max,
        "low_quality_bases": low_q,
    }


def align_trace_to_reference(trace_record: Dict[str, Any], reference_sequence: str) -> Dict[str, Any]:
    seq = _clean_dna(trace_record.get("sequence", ""))
    ref = _clean_dna(reference_sequence)
    if not seq or not ref:
        raise ValueError("trace and reference sequences are required")
    a = needleman_wunsch_simple(seq, ref)
    aligned_trace = a["aligned_a"]
    aligned_ref = a["aligned_b"]
    mismatches = []
    trace_pos = 0
    ref_pos = 0
    for t, r in zip(aligned_trace, aligned_ref):
        if t != "-":
            trace_pos += 1
        if r != "-":
            ref_pos += 1
        if t != "-" and r != "-" and t != r:
            mismatches.append({"trace_pos_1based": trace_pos, "ref_pos_1based": ref_pos, "trace_base": t, "ref_base": r})
    return {
        "trace_length": len(seq),
        "reference_length": len(ref),
        "score": a["score"],
        "identity_pct": a["identity_pct"],
        "aligned_trace": aligned_trace,
        "aligned_reference": aligned_ref,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:200],
    }


def edit_trace_base(trace_record: Dict[str, Any], position_1based: int, new_base: str, quality: int | None = None) -> Dict[str, Any]:
    seq = list(_clean_dna(trace_record.get("sequence", "")))
    if position_1based < 1 or position_1based > len(seq):
        raise ValueError("position out of range")
    b = _clean_dna(new_base)[:1]
    if b not in {"A", "C", "G", "T", "N"}:
        raise ValueError("new_base must be A/C/G/T/N")
    idx = position_1based - 1
    seq[idx] = b
    out = dict(trace_record)
    out["sequence"] = "".join(seq)
    q = [int(x) for x in out.get("quality", [])] if isinstance(out.get("quality", []), list) else [30] * len(seq)
    if len(q) < len(seq):
        q += [30] * (len(seq) - len(q))
    if quality is not None:
        q[idx] = max(0, min(99, int(quality)))
    out["quality"] = q
    out["length"] = len(seq)
    return out


def trace_consensus(trace_record: Dict[str, Any], min_quality: int = 20) -> Dict[str, Any]:
    seq = _clean_dna(trace_record.get("sequence", ""))
    q = [int(x) for x in trace_record.get("quality", [])] if isinstance(trace_record.get("quality", []), list) else []
    if len(q) < len(seq):
        q += [30] * (len(seq) - len(q))
    cons = []
    low = 0
    for b, qq in zip(seq, q):
        if qq < min_quality:
            cons.append("N")
            low += 1
        else:
            cons.append(b)
    c = "".join(cons)
    return {
        "length": len(c),
        "min_quality": int(min_quality),
        "low_quality_bases": low,
        "consensus": c,
    }

