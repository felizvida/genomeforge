from __future__ import annotations

import unittest

from backend.ngs_api import handle_ngs_endpoint, map_reads_to_reference, parse_fastq_text, trim_fastq_reads
from genomeforge_toolkit import SequenceRecord


EGFP_WINDOW = "ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTG"
ADAPTER = "AGATCGGAAGAGC"


def mutate(sequence: str, position_1based: int, alternate: str) -> str:
    return sequence[: position_1based - 1] + alternate + sequence[position_1based:]


def fastq_record(name: str, sequence: str, quality: str = "I") -> str:
    return f"@{name}\n{sequence}\n+\n{quality * len(sequence)}\n"


class NgsLiteWorkflowTests(unittest.TestCase):
    def test_fastq_trim_removes_adapter_and_low_quality_tail(self) -> None:
        read = EGFP_WINDOW[:36] + ADAPTER
        fastq = fastq_record("egfp_adapter_read", read, "I")
        reads = parse_fastq_text(fastq)
        trimmed = trim_fastq_reads(reads, adapter_sequence=ADAPTER, trim_quality=20, min_length=24)

        self.assertEqual(trimmed["kept_read_count"], 1)
        self.assertEqual(trimmed["trimmed_reads"][0]["sequence"], EGFP_WINDOW[:36])
        self.assertEqual(trimmed["qc_before"]["adapter_hit_count"], 1)
        self.assertEqual(trimmed["qc_after"]["adapter_hit_count"], 0)

    def test_ngs_mapping_calls_expected_reporter_variant(self) -> None:
        pos = 31
        alt = "A" if EGFP_WINDOW[pos - 1] != "A" else "C"
        variant_sequence = mutate(EGFP_WINDOW, pos, alt)
        reads = [
            {"name": "read_1", "sequence": variant_sequence[:36], "quality": "I" * 36},
            {"name": "read_2", "sequence": variant_sequence[12:48], "quality": "I" * 36},
            {"name": "read_3", "sequence": variant_sequence[24:60], "quality": "I" * 36},
        ]

        result = map_reads_to_reference(
            EGFP_WINDOW,
            parse_fastq_text("".join(fastq_record(row["name"], row["sequence"]) for row in reads)),
            max_mismatch_rate=0.08,
            min_depth=2,
            min_alt_count=2,
            min_alt_fraction=0.6,
        )

        self.assertEqual(result["mapped_read_count"], 3)
        self.assertGreaterEqual(result["covered_pct"], 90.0)
        self.assertEqual(result["variant_count"], 1)
        self.assertEqual(result["variants"][0]["position_1based"], pos)
        self.assertEqual(result["variants"][0]["alternate_base"], alt)

    def test_ngs_workflow_report_passes_expected_variant_after_trimming(self) -> None:
        pos = 31
        alt = "A" if EGFP_WINDOW[pos - 1] != "A" else "C"
        variant_sequence = mutate(EGFP_WINDOW, pos, alt)
        fastq = "".join(
            [
                fastq_record("read_1", variant_sequence[:36]),
                fastq_record("read_2", variant_sequence[12:48]),
                fastq_record("read_3", variant_sequence[24:60] + ADAPTER),
            ]
        )

        result = handle_ngs_endpoint(
            "/api/ngs-workflow-report",
            {
                "reference_sequence": EGFP_WINDOW,
                "fastq": fastq,
                "adapter_sequence": ADAPTER,
                "trim_quality": 20,
                "min_length": 24,
                "expected_variants": {str(pos): alt},
                "min_reference_coverage_pct": 90,
                "min_depth": 2,
                "min_alt_count": 2,
                "min_alt_fraction": 0.6,
            },
            lambda: SequenceRecord(name="EGFP_window", sequence=EGFP_WINDOW, topology="linear"),
        )

        assert result is not None
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["unexpected_variant_count"], 0)
        self.assertEqual(result["expected_variant_checks"][0]["status"], "pass")
        phases = {row["phase"]: row["status"] for row in result["replacement_phase_coverage"]}
        self.assertEqual(phases["NGS-lite local pipeline"], "pass")
        self.assertEqual(result["mapping"]["variant_count"], 1)

    def test_ngs_workflow_report_flags_unexpected_variant(self) -> None:
        pos = 31
        alt = "A" if EGFP_WINDOW[pos - 1] != "A" else "C"
        variant_sequence = mutate(EGFP_WINDOW, pos, alt)
        fastq = fastq_record("read_1", variant_sequence[:36]) + fastq_record("read_2", variant_sequence[12:48])

        result = handle_ngs_endpoint(
            "/api/ngs-workflow-report",
            {
                "reference_sequence": EGFP_WINDOW,
                "fastq": fastq,
                "min_reference_coverage_pct": 50,
                "min_depth": 2,
                "min_alt_count": 2,
                "min_alt_fraction": 0.6,
            },
            lambda: SequenceRecord(name="EGFP_window", sequence=EGFP_WINDOW, topology="linear"),
        )

        assert result is not None
        self.assertEqual(result["verdict"], "REVIEW")
        self.assertEqual(result["unexpected_variant_count"], 1)


if __name__ == "__main__":
    unittest.main()
