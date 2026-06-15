from __future__ import annotations

import base64
import json
import math
import uuid
from collections import Counter
from html import escape as html_escape
from typing import Any, Dict, List

from bio.trace_tools import align_trace_to_reference, edit_trace_base, trace_consensus, trace_summary
from compat.ab1_format import parse_ab1_bytes, synthetic_trace_from_sequence
from genomeforge_toolkit import DNA_ALPHABET, IUPAC_BASE_SETS


TRACE_CACHE: Dict[str, Dict[str, Any]] = {}


def _svg_text(value: object) -> str:
    return html_escape(str(value), quote=False)


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
        f'Trace chromatogram: {_svg_text(trace_record.get("trace_id", "trace"))}  {start_1based}..{end_1based} (step={step})</text>'
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


IUPAC_FROM_BASE_SET = {frozenset(v): k for k, v in IUPAC_BASE_SETS.items()}


def _consensus_base_from_counts(counts: Counter[str]) -> tuple[str, int, float]:
    if not counts:
        return "N", 0, 0.0
    ranked = counts.most_common()
    top_count = ranked[0][1]
    top_bases = sorted(base for base, count in ranked if count == top_count)
    total = sum(counts.values())
    if len(top_bases) == 1:
        return top_bases[0], top_count, round(100.0 * top_count / max(1, total), 2)
    return IUPAC_FROM_BASE_SET.get(frozenset(top_bases), "N"), top_count, round(100.0 * top_count / max(1, total), 2)


def _resolve_trace_collection(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    traces: List[Dict[str, Any]] = []
    trace_ids = payload.get("trace_ids", [])
    if isinstance(trace_ids, str):
        trace_ids = [item.strip() for item in trace_ids.split(",") if item.strip()]
    if isinstance(trace_ids, list):
        for trace_id in trace_ids:
            traces.append(_resolve_trace({"trace_id": str(trace_id)}))

    trace_records = payload.get("trace_records", payload.get("traces", []))
    if isinstance(trace_records, str):
        trace_records = json.loads(trace_records)
    if isinstance(trace_records, list):
        for trace_record in trace_records:
            if isinstance(trace_record, dict):
                traces.append(dict(trace_record))

    read_sequences = payload.get("read_sequences", payload.get("reads", []))
    if isinstance(read_sequences, str):
        read_sequences = [item.strip() for item in read_sequences.splitlines() if item.strip()]
    if isinstance(read_sequences, list):
        for sequence in read_sequences:
            traces.append(synthetic_trace_from_sequence(str(sequence)))

    cached = [_cache_trace(trace) for trace in traces]
    if not cached:
        raise ValueError("trace_ids, trace_records, or read_sequences are required")
    return cached


def sanger_multi_read_consensus(
    traces: List[Dict[str, Any]],
    reference_sequence: str,
    min_quality: int = 20,
    identity_threshold_pct: float = 85.0,
    min_called_pct: float = 80.0,
    genotype_positions: List[int] | None = None,
    expected_bases: Dict[str, str] | None = None,
    max_unexpected_variants: int = 0,
) -> Dict[str, Any]:
    reference = _clean_dna_string(reference_sequence)
    if not reference:
        raise ValueError("reference_sequence is required")
    if not traces:
        raise ValueError("at least one trace is required")

    votes: List[Counter[str]] = [Counter() for _ in reference]
    read_summaries: List[Dict[str, Any]] = []
    for trace in traces:
        consensus = trace_consensus(trace, min_quality=min_quality)
        consensus_seq = str(consensus.get("consensus", ""))
        alignment = align_trace_to_reference(trace, reference)
        trace_pos = 0
        ref_pos = 0
        covered_positions: List[int] = []
        for trace_base, ref_base in zip(str(alignment.get("aligned_trace", "")), str(alignment.get("aligned_reference", ""))):
            if trace_base != "-":
                trace_pos += 1
            if ref_base != "-":
                ref_pos += 1
            if trace_base == "-" or ref_base == "-":
                continue
            call = consensus_seq[trace_pos - 1] if trace_pos - 1 < len(consensus_seq) else "N"
            if call in {"A", "C", "G", "T"}:
                votes[ref_pos - 1][call] += 1
                covered_positions.append(ref_pos)
        read_summaries.append(
            {
                "trace_id": str(trace.get("trace_id", "")),
                "trace_length": int(alignment.get("trace_length", 0)),
                "identity_pct": float(alignment.get("identity_pct", 0.0)),
                "mismatch_count": int(alignment.get("mismatch_count", 0)),
                "low_quality_bases": int(consensus.get("low_quality_bases", 0)),
                "covered_reference_bases": len(set(covered_positions)),
                "reference_span": [min(covered_positions), max(covered_positions)] if covered_positions else [],
            }
        )

    consensus_chars: List[str] = []
    position_rows: List[Dict[str, Any]] = []
    variants: List[Dict[str, Any]] = []
    disagreements: List[Dict[str, Any]] = []
    for idx, counts in enumerate(votes, start=1):
        base, support, support_pct = _consensus_base_from_counts(counts)
        consensus_chars.append(base)
        depth = sum(counts.values())
        if depth:
            row = {
                "position_1based": idx,
                "reference_base": reference[idx - 1],
                "consensus_base": base,
                "depth": depth,
                "support": support,
                "support_pct": support_pct,
                "counts": dict(sorted(counts.items())),
            }
            position_rows.append(row)
            if len(counts) > 1:
                disagreements.append(row)
            base_set = IUPAC_BASE_SETS.get(base, frozenset())
            if base != "N" and base_set != frozenset({reference[idx - 1]}):
                variants.append(row)

    expected_bases = expected_bases or {}
    genotype_calls: List[Dict[str, Any]] = []
    for raw_pos in genotype_positions or []:
        pos = int(raw_pos)
        if pos < 1 or pos > len(reference):
            continue
        counts = votes[pos - 1]
        depth = sum(counts.values())
        base, support, support_pct = _consensus_base_from_counts(counts)
        expected = _clean_dna_string(str(expected_bases.get(str(pos), "")))[:1]
        base_set = IUPAC_BASE_SETS.get(base, frozenset())
        matches_expected = (expected in base_set) if expected and depth > 0 else (False if expected else None)
        genotype_calls.append(
            {
                "position_1based": pos,
                "reference_base": reference[pos - 1],
                "consensus_base": base,
                "expected_base": expected or None,
                "matches_expected": matches_expected,
                "status": "called" if depth > 0 else "no_coverage",
                "depth": depth,
                "support": support,
                "support_pct": support_pct,
                "counts": dict(sorted(counts.items())),
            }
        )

    expected_positions = {int(pos) for pos in expected_bases if str(pos).isdigit()}
    unexpected_variants = [variant for variant in variants if int(variant["position_1based"]) not in expected_positions]
    expected_failures = [call for call in genotype_calls if call.get("matches_expected") is False]
    low_identity_reads = [row for row in read_summaries if float(row["identity_pct"]) < float(identity_threshold_pct)]
    called_bases = sum(1 for counts in votes if counts)
    called_pct = round(100.0 * called_bases / max(1, len(reference)), 2)
    verdict_pass = (
        called_pct >= float(min_called_pct)
        and not low_identity_reads
        and len(unexpected_variants) <= int(max_unexpected_variants)
        and not expected_failures
    )
    return {
        "mode": "sanger_multi_read_consensus",
        "reference_length": len(reference),
        "read_count": len(traces),
        "min_quality": int(min_quality),
        "identity_threshold_pct": float(identity_threshold_pct),
        "min_called_pct": float(min_called_pct),
        "called_bases": called_bases,
        "called_pct": called_pct,
        "consensus_length": len(reference),
        "consensus": "".join(consensus_chars),
        "variant_count": len(variants),
        "unexpected_variant_count": len(unexpected_variants),
        "disagreement_count": len(disagreements),
        "genotype_call_count": len(genotype_calls),
        "variants": variants[:500],
        "unexpected_variants": unexpected_variants[:500],
        "disagreements": disagreements[:500],
        "genotype_calls": genotype_calls,
        "read_summaries": read_summaries,
        "verdict": "PASS" if verdict_pass else "FAIL",
        "failure_reasons": [
            reason
            for reason, failed in [
                ("called_pct_below_threshold", called_pct < float(min_called_pct)),
                ("low_identity_reads", bool(low_identity_reads)),
                ("unexpected_variants", len(unexpected_variants) > int(max_unexpected_variants)),
                ("expected_genotype_mismatch", bool(expected_failures)),
            ]
            if failed
        ],
    }


def trace_alignment_navigation(
    trace_record: Dict[str, Any],
    reference_sequence: str,
    flank: int = 24,
    max_rows: int = 800,
) -> Dict[str, Any]:
    align = align_trace_to_reference(trace_record, reference_sequence)
    aligned_trace = str(align.get("aligned_trace", ""))
    aligned_ref = str(align.get("aligned_reference", ""))
    trace_pos = 0
    ref_pos = 0
    rows: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    for column, (trace_base, ref_base) in enumerate(zip(aligned_trace, aligned_ref), start=1):
        if trace_base != "-":
            trace_pos += 1
        if ref_base != "-":
            ref_pos += 1
        status = "gap"
        if trace_base != "-" and ref_base != "-":
            status = "match" if trace_base == ref_base else "mismatch"
        row = {
            "alignment_column": column,
            "trace_pos_1based": trace_pos if trace_base != "-" else None,
            "ref_pos_1based": ref_pos if ref_base != "-" else None,
            "trace_base": trace_base,
            "reference_base": ref_base,
            "status": status,
        }
        rows.append(row)
        if row["trace_pos_1based"] and row["ref_pos_1based"]:
            t = int(row["trace_pos_1based"])
            r = int(row["ref_pos_1based"])
            links.append(
                {
                    **row,
                    "trace_window": [max(1, t - int(flank)), t + int(flank)],
                    "reference_window": [max(1, r - int(flank)), r + int(flank)],
                    "anchor": f"trace:{t}|ref:{r}",
                }
            )
    mismatch_links = [link for link in links if link["status"] == "mismatch"]
    sampled_links = links[:: max(1, len(links) // 120)] if len(links) > 160 else links
    navigation_links = sorted(
        {link["anchor"]: link for link in (mismatch_links + sampled_links)}.values(),
        key=lambda link: (int(link["ref_pos_1based"]), int(link["trace_pos_1based"])),
    )
    return {
        "trace_id": str(trace_record.get("trace_id", "")),
        "trace_length": align.get("trace_length", 0),
        "reference_length": align.get("reference_length", 0),
        "identity_pct": align.get("identity_pct", 0.0),
        "mismatch_count": align.get("mismatch_count", 0),
        "alignment_column_count": len(rows),
        "rows": rows[: max(1, int(max_rows))],
        "row_count": len(rows),
        "navigation_links": navigation_links[:300],
        "navigation_link_count": len(navigation_links),
        "mismatches": align.get("mismatches", []),
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
        nav = trace_alignment_navigation(
            trace,
            reference,
            flank=int(payload.get("flank", 24)),
            max_rows=int(payload.get("max_rows", 200)),
        )
        return {"trace_id": trace.get("trace_id"), **out, "navigation_link_count": nav["navigation_link_count"], "navigation_links": nav["navigation_links"]}

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

    if path == "/api/trace-alignment-links":
        trace = _cache_trace(_resolve_trace(payload))
        reference = str(payload.get("reference_sequence", payload.get("reference", "")))
        if not reference.strip():
            raise ValueError("reference_sequence is required")
        return trace_alignment_navigation(
            trace,
            reference,
            flank=int(payload.get("flank", 24)),
            max_rows=int(payload.get("max_rows", 800)),
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

    if path == "/api/sanger-consensus":
        reference = str(payload.get("reference_sequence", payload.get("reference", "")))
        if not reference.strip():
            raise ValueError("reference_sequence is required")
        genotype_positions = payload.get("genotype_positions", [])
        if isinstance(genotype_positions, str):
            genotype_positions = [int(x.strip()) for x in genotype_positions.split(",") if x.strip()]
        expected_bases = payload.get("expected_bases", {})
        if isinstance(expected_bases, str):
            expected_bases = json.loads(expected_bases)
        return sanger_multi_read_consensus(
            _resolve_trace_collection(payload),
            reference_sequence=reference,
            min_quality=int(payload.get("min_quality", 20)),
            identity_threshold_pct=float(payload.get("identity_threshold_pct", 85.0)),
            min_called_pct=float(payload.get("min_called_pct", 80.0)),
            genotype_positions=[int(x) for x in genotype_positions if isinstance(x, (int, float, str))],
            expected_bases={str(k): str(v) for k, v in dict(expected_bases).items()} if isinstance(expected_bases, dict) else {},
            max_unexpected_variants=int(payload.get("max_unexpected_variants", 0)),
        )

    return None
