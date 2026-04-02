from __future__ import annotations

import unittest

from genomeforge_toolkit import (
    SequenceRecord,
    design_primer_pair,
    find_all_occurrences,
    max_complement_run,
    optimize_coding_sequence,
    parse_feature_interval,
    parse_genbank,
    sanitize_sequence,
    simulate_pcr,
    simulate_digest,
)
from compat.ab1_format import synthetic_trace_from_sequence


EGFP_SEGMENT = (
    "ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAG"
    "TTCAGCGTGTCCGGCGAGGGCGAGGGCGATGCCACCTACGGCAAGCTGACCCTGAAGTTCATCTGCACCACCGGCAAGCTGC"
    "CCGTGCCCTGGCCCACCCTCGTGACCACCCTGACCTACGGCGTGCAGTGCTTCAGCCGCTACCCCGACCACATGAAGCAGCA"
)


class CoreAlgorithmTests(unittest.TestCase):
    def test_sanitize_sequence_normalizes_whitespace_and_case(self) -> None:
        self.assertEqual(sanitize_sequence(" atg c\nTt "), "ATGCTT")

    def test_sanitize_sequence_accepts_iupac_ambiguity_codes(self) -> None:
        self.assertEqual(sanitize_sequence(" aryswkmbdhvn "), "ARYSWKMBDHVN")

    def test_reverse_complement_preserves_iupac_ambiguity_codes(self) -> None:
        record = SequenceRecord(name="iupac", sequence="ARYSWKMBDHVN", topology="linear")
        self.assertEqual(record.reverse_complement().sequence, "NBDHVKMWSRYT")

    def test_parse_genbank_preserves_iupac_origin_symbols(self) -> None:
        record = parse_genbank(
            "LOCUS       IUPACSEQ                 12 bp    DNA     linear\n"
            "ORIGIN\n"
            "        1 atgryswkmbdh\n"
            "//\n"
        )
        self.assertEqual(record.sequence, "ATGRYSWKMBDH")

    def test_synthetic_trace_accepts_iupac_sequence(self) -> None:
        trace = synthetic_trace_from_sequence("ATGRYSWKMBDHVN")
        self.assertEqual(trace["sequence"], "ATGRYSWKMBDHVN")
        self.assertEqual(trace["length"], 14)

    def test_find_all_occurrences_matches_iupac_symbols_bidirectionally(self) -> None:
        self.assertEqual(find_all_occurrences("ATGRCC", "ATGGCC"), [0])
        self.assertEqual(find_all_occurrences("ATGGCC", "ATGRCC"), [0])

    def test_max_complement_run_counts_iupac_complementarity(self) -> None:
        self.assertEqual(max_complement_run("ATGR", "YCAT"), 4)

    def test_simulate_pcr_supports_iupac_template_matches(self) -> None:
        record = SequenceRecord(name="iupac_amplicon", sequence="ATGRCCGTTCA", topology="linear")
        result = simulate_pcr(record, forward_primer="ATGGCC", reverse_primer="TGAAC")
        self.assertEqual(result["forward_hits"], [1])
        self.assertEqual(result["reverse_hits"], [7])
        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["sequence"], "ATGRCCGTTCA")

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
