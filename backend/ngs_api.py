from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Any, Callable, Dict, List

from genomeforge_toolkit import DNA_ALPHABET, RC_TABLE, SequenceRecord, iupac_symbol_matches


RecordGetter = Callable[[], SequenceRecord]


@dataclass
class FastqRead:
    name: str
    sequence: str
    quality: str


def _clean_read_sequence(sequence: str) -> str:
    return "".join(ch for ch in str(sequence).upper() if ch in DNA_ALPHABET)


def _revcomp(sequence: str) -> str:
    return _clean_read_sequence(sequence).translate(RC_TABLE)[::-1]


def _quality_scores(quality: str) -> List[int]:
    return [max(0, min(60, ord(ch) - 33)) for ch in str(quality)]


def _quality_string(scores: List[int]) -> str:
    return "".join(chr(max(0, min(60, int(score))) + 33) for score in scores)


def parse_fastq_text(text: str, max_reads: int = 10000) -> List[FastqRead]:
    lines = [line.rstrip("\n\r") for line in str(text).splitlines() if line.strip()]
    if not lines:
        raise ValueError("FASTQ input is empty")
    if len(lines) % 4 != 0:
        raise ValueError("FASTQ input must contain complete 4-line records")
    reads: List[FastqRead] = []
    for offset in range(0, len(lines), 4):
        header, sequence, plus, quality = lines[offset : offset + 4]
        if not header.startswith("@"):
            raise ValueError(f"FASTQ record {offset // 4 + 1} header must start with @")
        if not plus.startswith("+"):
            raise ValueError(f"FASTQ record {offset // 4 + 1} separator must start with +")
        seq = _clean_read_sequence(sequence)
        if not seq:
            raise ValueError(f"FASTQ record {offset // 4 + 1} has no DNA bases")
        if len(quality) < len(seq):
            raise ValueError(f"FASTQ record {offset // 4 + 1} quality line is shorter than the sequence")
        reads.append(FastqRead(name=header[1:].strip() or f"read_{len(reads)+1}", sequence=seq, quality=quality[: len(seq)]))
        if len(reads) >= max_reads:
            break
    return reads


def reads_from_payload(payload: Dict[str, Any], max_reads: int = 10000) -> List[FastqRead]:
    fastq = str(payload.get("fastq", "")).strip()
    if fastq:
        return parse_fastq_text(fastq, max_reads=max_reads)
    raw_reads = payload.get("reads", payload.get("read_sequences", []))
    if isinstance(raw_reads, str):
        raw_reads = [line.strip() for line in raw_reads.splitlines() if line.strip()]
    reads: List[FastqRead] = []
    if isinstance(raw_reads, list):
        for idx, item in enumerate(raw_reads, start=1):
            if isinstance(item, dict):
                name = str(item.get("name", f"read_{idx}")).strip() or f"read_{idx}"
                seq = _clean_read_sequence(str(item.get("sequence", "")))
                quality = str(item.get("quality", "I" * len(seq)))
            else:
                name = f"read_{idx}"
                seq = _clean_read_sequence(str(item))
                quality = "I" * len(seq)
            if not seq:
                continue
            if len(quality) < len(seq):
                quality = quality + "!" * (len(seq) - len(quality))
            reads.append(FastqRead(name=name, sequence=seq, quality=quality[: len(seq)]))
            if len(reads) >= max_reads:
                break
    if not reads:
        raise ValueError("Provide fastq, reads, or read_sequences")
    return reads


def fastq_text_from_reads(reads: List[FastqRead]) -> str:
    chunks = []
    for read in reads:
        chunks.extend([f"@{read.name}", read.sequence, "+", read.quality])
    return "\n".join(chunks) + ("\n" if chunks else "")


def fastq_qc(reads: List[FastqRead], adapter_sequence: str = "") -> Dict[str, Any]:
    if not reads:
        raise ValueError("at least one read is required")
    lengths = [len(read.sequence) for read in reads]
    all_scores = [score for read in reads for score in _quality_scores(read.quality[: len(read.sequence)])]
    bases = "".join(read.sequence for read in reads)
    gc = sum(1 for base in bases if base in "GC")
    adapter = _clean_read_sequence(adapter_sequence)
    adapter_hits = sum(1 for read in reads if adapter and adapter in read.sequence)
    max_len = max(lengths)
    per_base_quality = []
    for pos in range(min(max_len, 250)):
        scores = []
        for read in reads:
            if pos < len(read.sequence) and pos < len(read.quality):
                scores.append(_quality_scores(read.quality[pos])[0])
        if scores:
            per_base_quality.append({"position_1based": pos + 1, "mean_quality": round(sum(scores) / len(scores), 3), "depth": len(scores)})
    warnings = []
    mean_q = sum(all_scores) / max(1, len(all_scores))
    if mean_q < 20:
        warnings.append("mean read quality is below Q20")
    if adapter_hits:
        warnings.append(f"adapter sequence detected in {adapter_hits} read(s)")
    if min(lengths) < 20:
        warnings.append("one or more reads are shorter than 20 bp")
    return {
        "mode": "fastq_qc",
        "read_count": len(reads),
        "base_count": sum(lengths),
        "length_min": min(lengths),
        "length_median": float(median(lengths)),
        "length_mean": round(sum(lengths) / len(lengths), 3),
        "length_max": max(lengths),
        "gc_pct": round(100.0 * gc / max(1, len(bases)), 3),
        "quality_mean": round(mean_q, 3),
        "q20_pct": round(100.0 * sum(1 for score in all_scores if score >= 20) / max(1, len(all_scores)), 3),
        "q30_pct": round(100.0 * sum(1 for score in all_scores if score >= 30) / max(1, len(all_scores)), 3),
        "adapter_sequence": adapter,
        "adapter_hit_count": adapter_hits,
        "per_base_quality": per_base_quality,
        "warnings": warnings,
    }


def trim_fastq_reads(
    reads: List[FastqRead],
    adapter_sequence: str = "AGATCGGAAGAGC",
    trim_quality: int = 20,
    min_length: int = 20,
) -> Dict[str, Any]:
    adapter = _clean_read_sequence(adapter_sequence)
    kept: List[FastqRead] = []
    dropped: List[Dict[str, Any]] = []
    trim_rows: List[Dict[str, Any]] = []
    for read in reads:
        seq = read.sequence
        scores = _quality_scores(read.quality[: len(seq)])
        original_length = len(seq)
        adapter_index = seq.find(adapter) if adapter else -1
        if adapter_index >= 0:
            seq = seq[:adapter_index]
            scores = scores[:adapter_index]
        left = 0
        right = len(seq)
        while left < right and scores[left] < trim_quality:
            left += 1
        while right > left and scores[right - 1] < trim_quality:
            right -= 1
        trimmed_seq = seq[left:right]
        trimmed_scores = scores[left:right]
        row = {
            "name": read.name,
            "original_length": original_length,
            "trimmed_length": len(trimmed_seq),
            "adapter_trimmed": adapter_index >= 0,
            "quality_left_trimmed_bp": left,
            "quality_right_trimmed_bp": len(seq) - right,
        }
        trim_rows.append(row)
        if len(trimmed_seq) < min_length:
            dropped.append({**row, "reason": "below_min_length"})
            continue
        kept.append(FastqRead(name=read.name, sequence=trimmed_seq, quality=_quality_string(trimmed_scores)))
    return {
        "mode": "fastq_trim",
        "input_read_count": len(reads),
        "kept_read_count": len(kept),
        "dropped_read_count": len(dropped),
        "trim_quality": int(trim_quality),
        "min_length": int(min_length),
        "adapter_sequence": adapter,
        "trimmed_reads": [{"name": read.name, "sequence": read.sequence, "quality": read.quality} for read in kept],
        "trimmed_fastq": fastq_text_from_reads(kept),
        "trim_rows": trim_rows,
        "dropped_reads": dropped,
        "qc_before": fastq_qc(reads, adapter_sequence=adapter),
        "qc_after": fastq_qc(kept, adapter_sequence=adapter) if kept else None,
    }


def _mismatch_count(reference_window: str, read: str) -> int:
    return sum(1 for ref_base, read_base in zip(reference_window, read) if not iupac_symbol_matches(ref_base, read_base))


def _best_mapping(reference: str, read: FastqRead, max_mismatches: int) -> Dict[str, Any] | None:
    if len(read.sequence) > len(reference):
        return None
    best: Dict[str, Any] | None = None
    candidates = [("+", read.sequence, read.quality), ("-", _revcomp(read.sequence), read.quality[::-1])]
    for strand, seq, quality in candidates:
        for start in range(0, len(reference) - len(seq) + 1):
            window = reference[start : start + len(seq)]
            mismatches = _mismatch_count(window, seq)
            if best is None or mismatches < int(best["mismatches"]):
                best = {"strand": strand, "start_0based": start, "sequence": seq, "quality": quality, "mismatches": mismatches}
                if mismatches == 0:
                    break
        if best is not None and int(best["mismatches"]) == 0:
            break
    if best is None or int(best["mismatches"]) > max_mismatches:
        return None
    return best


def _zero_coverage_regions(coverage: List[int], max_regions: int = 20) -> List[Dict[str, int]]:
    regions: List[Dict[str, int]] = []
    start = None
    for idx, depth in enumerate(coverage, start=1):
        if depth == 0 and start is None:
            start = idx
        if depth > 0 and start is not None:
            regions.append({"start_1based": start, "end_1based": idx - 1, "length_bp": idx - start})
            start = None
    if start is not None:
        regions.append({"start_1based": start, "end_1based": len(coverage), "length_bp": len(coverage) - start + 1})
    return regions[:max_regions]


def map_reads_to_reference(
    reference_sequence: str,
    reads: List[FastqRead],
    max_mismatch_rate: float = 0.08,
    min_base_quality: int = 20,
    min_depth: int = 2,
    min_alt_count: int = 2,
    min_alt_fraction: float = 0.6,
) -> Dict[str, Any]:
    reference = _clean_read_sequence(reference_sequence)
    if not reference:
        raise ValueError("reference_sequence is required")
    coverage = [0] * len(reference)
    base_counts: List[Dict[str, int]] = [{base: 0 for base in "ACGT"} for _ in reference]
    rows: List[Dict[str, Any]] = []
    mapped = 0
    for read in reads:
        allowed_mismatches = max(0, int(math.floor(len(read.sequence) * float(max_mismatch_rate))))
        hit = _best_mapping(reference, read, max_mismatches=allowed_mismatches)
        if hit is None:
            rows.append({"name": read.name, "length": len(read.sequence), "mapped": False, "reason": "no_hit_within_mismatch_limit"})
            continue
        mapped += 1
        seq = str(hit["sequence"])
        qual = str(hit["quality"])
        start = int(hit["start_0based"])
        high_quality_bases = 0
        for offset, base in enumerate(seq):
            pos = start + offset
            q = _quality_scores(qual[offset])[0] if offset < len(qual) else 0
            if q < min_base_quality or base not in "ACGT":
                continue
            coverage[pos] += 1
            base_counts[pos][base] += 1
            high_quality_bases += 1
        rows.append(
            {
                "name": read.name,
                "length": len(read.sequence),
                "mapped": True,
                "start_1based": start + 1,
                "end_1based": start + len(seq),
                "strand": hit["strand"],
                "mismatches": int(hit["mismatches"]),
                "identity_pct": round(100.0 * (len(seq) - int(hit["mismatches"])) / max(1, len(seq)), 3),
                "high_quality_bases": high_quality_bases,
            }
        )
    variants = []
    consensus_chars = []
    for idx, ref_base in enumerate(reference):
        counts = base_counts[idx]
        depth = sum(counts.values())
        if depth == 0:
            consensus_chars.append("N")
            continue
        consensus_base = max("ACGT", key=lambda base: (counts[base], base == ref_base))
        consensus_chars.append(consensus_base)
        for base in "ACGT":
            if base == ref_base:
                continue
            alt_count = counts[base]
            alt_fraction = alt_count / max(1, depth)
            if depth >= min_depth and alt_count >= min_alt_count and alt_fraction >= min_alt_fraction:
                variants.append(
                    {
                        "position_1based": idx + 1,
                        "reference_base": ref_base,
                        "alternate_base": base,
                        "depth": depth,
                        "alt_count": alt_count,
                        "alt_fraction": round(alt_fraction, 4),
                        "counts": dict(counts),
                    }
                )
    covered_bases = sum(1 for depth in coverage if depth > 0)
    mean_depth = sum(coverage) / max(1, len(coverage))
    return {
        "mode": "ngs_lite_read_mapping",
        "reference_length": len(reference),
        "read_count": len(reads),
        "mapped_read_count": mapped,
        "unmapped_read_count": len(reads) - mapped,
        "mapped_pct": round(100.0 * mapped / max(1, len(reads)), 3),
        "covered_bases": covered_bases,
        "covered_pct": round(100.0 * covered_bases / max(1, len(reference)), 3),
        "mean_depth": round(mean_depth, 3),
        "max_depth": max(coverage) if coverage else 0,
        "min_base_quality": int(min_base_quality),
        "max_mismatch_rate": float(max_mismatch_rate),
        "coverage": coverage,
        "zero_coverage_regions": _zero_coverage_regions(coverage),
        "consensus": "".join(consensus_chars),
        "variant_count": len(variants),
        "variants": variants,
        "read_mappings": rows,
    }


def ngs_workflow_report(payload: Dict[str, Any], get_record: RecordGetter) -> Dict[str, Any]:
    reference = str(payload.get("reference_sequence", "")).strip()
    if not reference:
        reference = get_record().sequence
    adapter = str(payload.get("adapter_sequence", "AGATCGGAAGAGC"))
    reads = reads_from_payload(payload)
    trim = trim_fastq_reads(
        reads,
        adapter_sequence=adapter,
        trim_quality=int(payload.get("trim_quality", 20)),
        min_length=int(payload.get("min_length", 20)),
    )
    trimmed_reads = [
        FastqRead(name=str(row["name"]), sequence=str(row["sequence"]), quality=str(row["quality"]))
        for row in trim.get("trimmed_reads", [])
    ]
    mapping = map_reads_to_reference(
        reference,
        trimmed_reads,
        max_mismatch_rate=float(payload.get("max_mismatch_rate", 0.08)),
        min_base_quality=int(payload.get("min_base_quality", 20)),
        min_depth=int(payload.get("min_depth", 2)),
        min_alt_count=int(payload.get("min_alt_count", 2)),
        min_alt_fraction=float(payload.get("min_alt_fraction", 0.6)),
    )
    expected_variants = payload.get("expected_variants", payload.get("expected_bases", {}))
    if isinstance(expected_variants, str):
        import json

        expected_variants = json.loads(expected_variants) if expected_variants.strip() else {}
    expected_checks = []
    for pos_key, expected_base_raw in dict(expected_variants or {}).items():
        pos = int(pos_key)
        expected_base = _clean_read_sequence(str(expected_base_raw))[:1]
        if pos < 1 or pos > int(mapping["reference_length"]):
            expected_checks.append({"position_1based": pos, "expected_base": expected_base, "status": "out_of_range"})
            continue
        observed = str(mapping["consensus"])[pos - 1]
        depth = int(mapping["coverage"][pos - 1])
        expected_checks.append(
            {
                "position_1based": pos,
                "expected_base": expected_base,
                "observed_base": observed,
                "depth": depth,
                "status": "pass" if depth > 0 and observed == expected_base else ("no_coverage" if depth == 0 else "mismatch"),
            }
        )
    expected_positions = {int(row["position_1based"]) for row in expected_checks if row.get("status") == "pass"}
    unexpected_variants = [
        row
        for row in mapping["variants"]
        if int(row["position_1based"]) not in expected_positions
    ]
    min_coverage_pct = float(payload.get("min_reference_coverage_pct", 90.0))
    max_unexpected = int(payload.get("max_unexpected_variants", 0))
    expected_ok = all(row.get("status") == "pass" for row in expected_checks)
    coverage_ok = float(mapping["covered_pct"]) >= min_coverage_pct
    unexpected_ok = len(unexpected_variants) <= max_unexpected
    qc_after = trim.get("qc_after") or {}
    qc_ok = bool(qc_after) and float(qc_after.get("quality_mean", 0.0)) >= float(payload.get("min_mean_quality", 25.0))
    phase_coverage = [
        {
            "phase": "SnapGene-style construct verification",
            "status": "pass" if expected_ok and unexpected_ok else "review",
            "evidence": f"{len(expected_checks)} expected locus/loci checked; {len(unexpected_variants)} unexpected variant(s).",
        },
        {
            "phase": "Geneious-style sequence analysis",
            "status": "pass" if mapping["mapped_read_count"] else "fail",
            "evidence": f"{mapping['mapped_read_count']}/{mapping['read_count']} reads mapped with {mapping['covered_pct']}% reference coverage.",
        },
        {
            "phase": "NGS-lite local pipeline",
            "status": "pass" if qc_ok and coverage_ok else "review",
            "evidence": f"Qmean {qc_after.get('quality_mean', 0)} after trimming; mean depth {mapping['mean_depth']}.",
        },
        {
            "phase": "Trust and release evidence",
            "status": "pass",
            "evidence": "Report includes read QC, trimming audit, mapping rows, coverage, variants, and explicit decision checks.",
        },
    ]
    verdict = "PASS" if qc_ok and coverage_ok and expected_ok and unexpected_ok else "REVIEW"
    return {
        "mode": "ngs_lite_workflow_report",
        "verdict": verdict,
        "qc_before": trim["qc_before"],
        "trim": {k: v for k, v in trim.items() if k not in {"trimmed_fastq", "trimmed_reads"}},
        "mapping": mapping,
        "expected_variant_checks": expected_checks,
        "unexpected_variant_count": len(unexpected_variants),
        "unexpected_variants": unexpected_variants,
        "replacement_phase_coverage": phase_coverage,
    }


def handle_ngs_endpoint(path: str, payload: Dict[str, Any], get_record: RecordGetter) -> Dict[str, Any] | None:
    if path == "/api/fastq-qc":
        reads = reads_from_payload(payload)
        return fastq_qc(reads, adapter_sequence=str(payload.get("adapter_sequence", "AGATCGGAAGAGC")))
    if path == "/api/fastq-trim":
        return trim_fastq_reads(
            reads_from_payload(payload),
            adapter_sequence=str(payload.get("adapter_sequence", "AGATCGGAAGAGC")),
            trim_quality=int(payload.get("trim_quality", 20)),
            min_length=int(payload.get("min_length", 20)),
        )
    if path == "/api/ngs-map-reads":
        reference = str(payload.get("reference_sequence", "")).strip() or get_record().sequence
        return map_reads_to_reference(
            reference,
            reads_from_payload(payload),
            max_mismatch_rate=float(payload.get("max_mismatch_rate", 0.08)),
            min_base_quality=int(payload.get("min_base_quality", 20)),
            min_depth=int(payload.get("min_depth", 2)),
            min_alt_count=int(payload.get("min_alt_count", 2)),
            min_alt_fraction=float(payload.get("min_alt_fraction", 0.6)),
        )
    if path == "/api/ngs-workflow-report":
        return ngs_workflow_report(payload, get_record)
    return None
