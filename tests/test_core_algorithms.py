from __future__ import annotations

import unittest

from genomeforge_toolkit import (
    SequenceRecord,
    design_primer_pair,
    optimize_coding_sequence,
    parse_feature_interval,
    sanitize_sequence,
    simulate_digest,
)


EGFP_SEGMENT = (
    "ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAG"
    "TTCAGCGTGTCCGGCGAGGGCGAGGGCGATGCCACCTACGGCAAGCTGACCCTGAAGTTCATCTGCACCACCGGCAAGCTGC"
    "CCGTGCCCTGGCCCACCCTCGTGACCACCCTGACCTACGGCGTGCAGTGCTTCAGCCGCTACCCCGACCACATGAAGCAGCA"
)


class CoreAlgorithmTests(unittest.TestCase):
    def test_sanitize_sequence_normalizes_whitespace_and_case(self) -> None:
        self.assertEqual(sanitize_sequence(" atg c\nTt "), "ATGCTT")

    def test_parse_feature_interval_handles_reverse_order(self) -> None:
        self.assertEqual(parse_feature_interval("complement(80..12)"), (12, 80))

    def test_simulate_digest_reports_expected_cut_positions(self) -> None:
        record = SequenceRecord(name="pDemo", sequence="GAATTCCGGATCC", topology="linear")
        result = simulate_digest(record, ["EcoRI", "BamHI"])
        self.assertEqual(result["unique_cut_positions_1based"], [2, 9])
        self.assertEqual(result["fragments_bp"], [7, 5, 1])

    def test_optimize_coding_sequence_preserves_protein_length(self) -> None:
        result = optimize_coding_sequence("ATGGCCGAACTGTAA", host="ecoli")
        self.assertEqual(result["protein"], "MAEL*")
        self.assertEqual(len(result["optimized_nt"]), 15)

    def test_design_primer_pair_returns_amplicon_metadata(self) -> None:
        record = SequenceRecord(name="egfp_segment", sequence=EGFP_SEGMENT, topology="linear")
        result = design_primer_pair(
            record,
            target_start_1based=60,
            target_end_1based=240,
            min_len=20,
            max_len=25,
            window=60,
            tm_min=55.0,
            tm_max=68.0,
        )
        self.assertGreater(result["amplicon_bp"], 0)
        self.assertIn("sequence", result["forward"])
        self.assertIn("sequence", result["reverse"])


if __name__ == "__main__":
    unittest.main()
