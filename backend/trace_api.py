from __future__ import annotations

import base64
import json
import math
import uuid
from typing import Any, Dict, List

from bio.trace_tools import align_trace_to_reference, edit_trace_base, trace_consensus, trace_summary
from compat.ab1_format import parse_ab1_bytes, synthetic_trace_from_sequence
from genomeforge_toolkit import DNA_ALPHABET


TRACE_CACHE: Dict[str, Dict[str, Any]] = {}


def _decode_b64_field(value: str, label: str) -> bytes:
    if not value:
        raise ValueError(f"{label} is required")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{label} must be valid base64: {exc}") from exc


def _clean_dna_string(seq: str) -> str:
    return "".join(ch for ch in str(seq).upper() if ch in DNA_ALPHABET)


def _cache_trace(trace_record: Dict[str, Any]) -> Dict[str, Any]:
    tid = str(trace_record.get("trace_id", "")).strip()
    if not tid:
        tid = "trace_" + uuid.uuid4().hex[:12]
        trace_record["trace_id"] = tid
    TRACE_CACHE[tid] = trace_record
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


def trace_chromatogram_svg(
    trace_record: Dict[str, Any],
    start_1based: int = 1,
    end_1based: int = 0,
    max_points: int = 400,
) -> Dict[str, Any]:
    seq = _clean_dna_string(trace_record.get("sequence", ""))
    if not seq:
        raise ValueError("trace sequence is empty")
    n = len(seq)
    start_1based = max(1, int(start_1based))
    end_1based = n if int(end_1based) <= 0 else min(n, int(end_1based))
    if start_1based > end_1based:
        raise ValueError("Invalid trace range")
    width = 1240
    height = 280
    margin_l = 70
    margin_r = 20
    margin_t = 26
    margin_b = 32
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    traces = trace_record.get("traces", {})
    if not isinstance(traces, dict):
        traces = {}
    channels = {b: [int(v) for v in traces.get(b, []) if isinstance(v, (int, float))] for b in "ACGT"}
    max_trace_len = max([len(channels[b]) for b in "ACGT"] + [n])
    positions_raw = trace_record.get("positions", [])
    if isinstance(positions_raw, list):
        positions = [int(v) for v in positions_raw[:n] if isinstance(v, (int, float))]
    else:
        positions = []
    if len(positions) < n:
        positions = list(range(1, n + 1))

    base_start_idx = start_1based - 1
    base_end_idx = end_1based - 1
    left_sample = max(0, positions[base_start_idx] - 1)
    right_sample = max(0, positions[base_end_idx] - 1)
    pad = 8
    sample_start = max(0, min(left_sample, max_trace_len - 1) - pad)
    sample_end = min(max_trace_len - 1, max(right_sample, 0) + pad)
    sample_span = max(1, sample_end - sample_start + 1)
    step = max(1, int(math.ceil(sample_span / max(50, int(max_points)))))
    idxs = list(range(sample_start, sample_end + 1, step))
    max_signal = 1
    for base in "ACGT":
        for i in idxs:
            if i < len(channels[base]):
                max_signal = max(max_signal, channels[base][i])

    def x_for(sample_idx0: int) -> float:
        return margin_l + (sample_idx0 - sample_start) * plot_w / max(1, sample_span - 1)

    def y_for(v: int) -> float:
        return margin_t + plot_h - (v / max_signal) * plot_h

    colors = {"A": "#22c55e", "C": "#2563eb", "G": "#111827", "T": "#ef4444"}
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    lines.append('<rect width="100%" height="100%" fill="#f8fafc"/>')
    lines.append(
        f'<text x="{margin_l}" y="18" font-size="13" font-family="Menlo, monospace" fill="#0f172a">'
        f'Trace chromatogram: {trace_record.get("trace_id", "trace")}  {start_1based}..{end_1based} (step={step})</text>'
    )
    lines.append(f'<rect x="{margin_l}" y="{margin_t}" width="{plot_w}" height="{plot_h}" fill="#ffffff" stroke="#dbe5f3"/>')
    for base in "ACGT":
        pts = []
        for i in idxs:
            signal = channels[base][i] if i < len(channels[base]) else 0
            pts.append(f"{x_for(i):.2f},{y_for(signal):.2f}")
        lines.append(
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{colors[base]}" stroke-width="1.8">'
            f"<title>{base} signal</title></polyline>"
        )
    if (end_1based - start_1based + 1) <= 120:
        for base_idx in range(start_1based, end_1based + 1):
            peak_x = x_for(max(0, positions[base_idx - 1] - 1))
            lines.append(
                f'<text x="{peak_x:.2f}" y="{margin_t + 12}" text-anchor="middle" font-size="9" '
                f'font-family="Menlo, monospace" fill="{colors.get(seq[base_idx - 1], "#334155")}">{seq[base_idx - 1]}</text>'
            )
    for tick in range(6):
        pos = int(round(start_1based + tick * (end_1based - start_1based) / 5))
        x = x_for(max(0, positions[pos - 1] - 1))
        lines.append(f'<line x1="{x:.2f}" y1="{margin_t + plot_h}" x2="{x:.2f}" y2="{margin_t + plot_h + 6}" stroke="#334155"/>')
        lines.append(
            f'<text x="{x:.2f}" y="{margin_t + plot_h + 20}" text-anchor="middle" font-size="10" '
            f'font-family="Menlo, monospace" fill="#334155">{pos}</text>'
        )
    lines.append(
        f'<text x="{margin_l}" y="{height-6}" font-size="10" font-family="Menlo, monospace" fill="#334155">'
        f'A=green C=blue G=black T=red</text>'
    )
    lines.append("</svg>")
    return {
        "trace_id": str(trace_record.get("trace_id", "")),
        "start_1based": start_1based,
        "end_1based": end_1based,
        "points": len(idxs),
        "max_signal": max_signal,
        "sample_start_index_0based": sample_start,
        "sample_end_index_0based": sample_end,
        "svg": "\n".join(lines),
    }


def trace_verify_genotype(
    trace_record: Dict[str, Any],
    reference_sequence: str,
    min_quality: int = 20,
    genotype_positions: List[int] | None = None,
    expected_bases: Dict[str, str] | None = None,
    identity_threshold_pct: float = 98.0,
    max_mismatches: int = 5,
) -> Dict[str, Any]:
    ref = _clean_dna_string(reference_sequence)
    if not ref:
        raise ValueError("reference_sequence is required")
    trace = dict(trace_record)
    align = align_trace_to_reference(trace, ref)
    consensus = trace_consensus(trace, min_quality=min_quality)
    cseq = consensus["consensus"]
    mapping: Dict[int, Dict[str, Any]] = {}
    tpos = 0
    rpos = 0
    aligned_t = align["aligned_trace"]
    aligned_r = align["aligned_reference"]
    for tb, rb in zip(aligned_t, aligned_r):
        if tb != "-":
            tpos += 1
        if rb != "-":
            rpos += 1
        if tb != "-" and rb != "-":
            cb = cseq[tpos - 1] if tpos - 1 < len(cseq) else "N"
            mapping[rpos] = {
                "trace_pos_1based": tpos,
                "trace_base": tb,
                "consensus_base": cb,
                "reference_base": rb,
            }

    expected_bases = expected_bases or {}
    calls = []
    for raw_pos in genotype_positions or []:
        pos = int(raw_pos)
        if pos < 1 or pos > len(ref):
            continue
        hit = mapping.get(pos)
        expected = _clean_dna_string(str(expected_bases.get(str(pos), "")))[:1]
        if not hit:
            calls.append({"position_1based": pos, "reference_base": ref[pos - 1], "call": "NO_COVERAGE", "matches_expected": False})
            continue
        call = hit["consensus_base"]
        calls.append(
            {
                "position_1based": pos,
                "reference_base": ref[pos - 1],
                "trace_base": hit["trace_base"],
                "consensus_base": call,
                "expected_base": expected or None,
                "matches_expected": (call == expected) if expected else None,
                "trace_pos_1based": hit["trace_pos_1based"],
            }
        )

    mismatch_count = int(align.get("mismatch_count", 0))
    call_failures = sum(1 for call in calls if call.get("matches_expected") is False)
    verdict_pass = (
        float(align.get("identity_pct", 0.0)) >= float(identity_threshold_pct)
        and mismatch_count <= int(max_mismatches)
        and call_failures == 0
    )
    return {
        "trace_id": str(trace.get("trace_id", "")),
        "reference_length": len(ref),
        "identity_pct": align.get("identity_pct", 0.0),
        "mismatch_count": mismatch_count,
        "min_quality": int(min_quality),
        "consensus_low_quality_bases": consensus.get("low_quality_bases", 0),
        "identity_threshold_pct": float(identity_threshold_pct),
        "max_mismatches": int(max_mismatches),
        "genotype_call_count": len(calls),
        "genotype_calls": calls,
        "verdict": "PASS" if verdict_pass else "FAIL",
    }


def handle_trace_endpoint(path: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
    if path == "/api/import-ab1":
        if str(payload.get("ab1_base64", "")).strip():
            raw = _decode_b64_field(str(payload.get("ab1_base64", "")).strip(), "ab1_base64")
            trace = parse_ab1_bytes(raw)
        elif str(payload.get("sequence", "")).strip():
            trace = synthetic_trace_from_sequence(str(payload.get("sequence", "")))
        else:
            raise ValueError("ab1_base64 or sequence is required")
        trace = _cache_trace(trace)
        return {"trace_record": trace, "summary": trace_summary(trace)}

    if path == "/api/trace-summary":
        trace = _cache_trace(_resolve_trace(payload))
        return {"trace_record": trace, "summary": trace_summary(trace)}

    if path == "/api/trace-align":
        trace = _resolve_trace(payload)
        reference = str(payload.get("reference_sequence", payload.get("reference", "")))
        if not reference.strip():
            raise ValueError("reference_sequence is required")
        out = align_trace_to_reference(trace, reference)
        trace = _cache_trace(trace)
        return {"trace_id": trace.get("trace_id"), **out}

    if path == "/api/trace-edit-base":
        trace = _resolve_trace(payload)
        edited = edit_trace_base(
            trace,
            position_1based=int(payload.get("position_1based", 1)),
            new_base=str(payload.get("new_base", "N")),
            quality=(int(payload["quality"]) if "quality" in payload and payload.get("quality") is not None else None),
        )
        edited = _cache_trace(edited)
        return {"trace_record": edited, "summary": trace_summary(edited)}

    if path == "/api/trace-consensus":
        trace = _cache_trace(_resolve_trace(payload))
        return {"trace_id": trace.get("trace_id"), **trace_consensus(trace, min_quality=int(payload.get("min_quality", 20)))}

    if path == "/api/trace-chromatogram-svg":
        trace = _cache_trace(_resolve_trace(payload))
        return trace_chromatogram_svg(
            trace,
            start_1based=int(payload.get("start", 1)),
            end_1based=int(payload.get("end", 0)),
            max_points=int(payload.get("max_points", 400)),
        )

    if path == "/api/trace-verify":
        trace = _cache_trace(_resolve_trace(payload))
        reference = str(payload.get("reference_sequence", payload.get("reference", "")))
        if not reference.strip():
            raise ValueError("reference_sequence is required")
        genotype_positions = payload.get("genotype_positions", [])
        if isinstance(genotype_positions, str):
            genotype_positions = [int(x.strip()) for x in genotype_positions.split(",") if x.strip()]
        expected_bases = payload.get("expected_bases", {})
        if isinstance(expected_bases, str):
            expected_bases = json.loads(expected_bases)
        return trace_verify_genotype(
            trace,
            reference_sequence=reference,
            min_quality=int(payload.get("min_quality", 20)),
            genotype_positions=[int(x) for x in genotype_positions if isinstance(x, (int, float, str))],
            expected_bases={str(k): str(v) for k, v in dict(expected_bases).items()} if isinstance(expected_bases, dict) else {},
            identity_threshold_pct=float(payload.get("identity_threshold_pct", 98.0)),
            max_mismatches=int(payload.get("max_mismatches", 5)),
        )

    return None
