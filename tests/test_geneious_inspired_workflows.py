from __future__ import annotations

import unittest

from backend.search_reference_api import handle_search_reference_endpoint
from backend.trace_api import handle_trace_endpoint
from genomeforge_toolkit import SequenceRecord


EGFP_CDS = (
    "ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAG"
    "TTCAGCGTGTCCGGCGAGGGCGAGGGCGAGGGCGATGCCACCTACGGCAAGCTGACCCTGAAGTTCATCTGCACCACCGGCA"
    "AGCTGCCCGTGCCCTGGCCCACCCTCGTGACCACCCTGACCTACGGCGTGCAGTGCTTCAGCCGCTACCCCGACCACATGA"
    "AGCAGCACGACTTCTTCAAGTCCGCCATGCCCGAAGGCTACGTCCAGGAGCGCACCATCTTCTTCAAGGACGACGGCAACT"
    "ACAAGACCCGCGCCGAGGTGAAGTTCGAGGGCGACACCCTGGTGAACCGCATCGAGCTGAAGGGCATCGACTTCAAGGAGG"
    "ACGGCAACATCCTGGGGCACAAGCTGGAGTACAACTACAACAGCCACAACGTCTATATCATGGCCGACAAGCAGAAGAACG"
    "GCATCAAGGTGAACTTCAAGATCCGCCACAACATCGAGGACGGCAGCGTGCAGCTCGCCGACCACTACCAGCAGAACACCC"
    "CCATCGGCGACGGCCCCGTGCTGCTGCCCGACAACCACTACCTGAGCACCCAGTCCAAGCTGAGCAAAGACCCCAACGAGA"
    "AGCGCGATCACATGGTCCTGCTGGAGTTCGTGACCGCCGCCGGGATCACTCTCGGCATGGACGAGCTGTACAAGTAA"
)

PUC19_MCS = "GAATTCGAGCTCGGTACCCGGGGATCCTCTAGAGTCGACCTGCAGGCATGCAAGCTT"


class GeneiousInspiredWorkflowTests(unittest.TestCase):
    def test_similarity_annotation_transfer_marks_reporter_insert(self) -> None:
        target = SequenceRecord(
            name="pUC19_EGFP_candidate",
            sequence=PUC19_MCS + EGFP_CDS,
            topology="circular",
        )
        result = handle_search_reference_endpoint(
            "/api/annotation-transfer",
            {
                "reference_records": [
                    {
                        "name": "EGFP_CDS_reference",
                        "sequence": EGFP_CDS,
                        "features": [
                            {
                                "key": "CDS",
                                "location": f"1..{len(EGFP_CDS)}",
                                "qualifiers": {"label": "EGFP reporter CDS", "codon_start": "1"},
                            },
                            {
                                "key": "gene",
                                "location": "1..60",
                                "qualifiers": {"label": "gfp N-terminus"},
                            },
                        ],
                    }
                ],
                "min_identity_pct": 98.0,
                "min_feature_coverage_pct": 95.0,
                "add_features": True,
            },
            lambda: target,
        )
        assert result is not None
        self.assertEqual(result["transferred_count"], 2)
        self.assertEqual(result["features_added"], 2)
        cds = [row for row in result["transferred_features"] if row["key"] == "CDS"][0]
        self.assertEqual(cds["start_1based"], len(PUC19_MCS) + 1)
        self.assertEqual(cds["end_1based"], len(PUC19_MCS) + len(EGFP_CDS))
        self.assertGreaterEqual(cds["identity_pct"], 99.0)
        self.assertTrue(any(feature["qualifiers"]["label"] == "EGFP reporter CDS" for feature in result["features"]))

    def test_sanger_multi_read_consensus_verifies_expected_reporter_variant(self) -> None:
        reference = EGFP_CDS[:240]
        variant_pos = 67
        variant_base = "C" if reference[variant_pos - 1] != "C" else "A"
        variant = reference[: variant_pos - 1] + variant_base + reference[variant_pos:]
        mixed_read = reference

        result = handle_trace_endpoint(
            "/api/sanger-consensus",
            {
                "reference_sequence": reference,
                "read_sequences": [variant, variant, mixed_read],
                "genotype_positions": [variant_pos],
                "expected_bases": {str(variant_pos): variant_base},
                "min_quality": 20,
                "identity_threshold_pct": 98.0,
                "min_called_pct": 100.0,
                "max_unexpected_variants": 0,
            },
        )
        assert result is not None
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["read_count"], 3)
        self.assertEqual(result["called_pct"], 100.0)
        self.assertEqual(result["variant_count"], 1)
        self.assertEqual(result["unexpected_variant_count"], 0)
        self.assertEqual(result["disagreement_count"], 1)
        self.assertEqual(result["genotype_calls"][0]["matches_expected"], True)

    def test_sanger_multi_read_consensus_fails_unexpected_variant(self) -> None:
        reference = EGFP_CDS[:180]
        variant_pos = 42
        variant_base = "T" if reference[variant_pos - 1] != "T" else "G"
        variant = reference[: variant_pos - 1] + variant_base + reference[variant_pos:]

        result = handle_trace_endpoint(
            "/api/sanger-consensus",
            {
                "reference_sequence": reference,
                "read_sequences": [variant, variant],
                "min_called_pct": 100.0,
                "max_unexpected_variants": 0,
            },
        )
        assert result is not None
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["unexpected_variant_count"], 1)
        self.assertIn("unexpected_variants", result["failure_reasons"])

    def test_sanger_multi_read_consensus_fails_expected_position_without_coverage(self) -> None:
        reference = "A" * 20 + "C" * 20 + "G" * 20 + "T" * 20 + "ACGTACGTACGTACGTACGT"
        read = reference[:80]
        genotype_pos = 95

        result = handle_trace_endpoint(
            "/api/sanger-consensus",
            {
                "reference_sequence": reference,
                "read_sequences": [read],
                "genotype_positions": [genotype_pos],
                "expected_bases": {str(genotype_pos): reference[genotype_pos - 1]},
                "min_called_pct": 80.0,
                "identity_threshold_pct": 80.0,
                "max_unexpected_variants": 0,
            },
        )
        assert result is not None
        self.assertEqual(result["called_pct"], 80.0)
        self.assertEqual(result["genotype_calls"][0]["depth"], 0)
        self.assertEqual(result["genotype_calls"][0]["status"], "no_coverage")
        self.assertEqual(result["genotype_calls"][0]["matches_expected"], False)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIn("expected_genotype_mismatch", result["failure_reasons"])

    def test_similarity_annotation_transfer_rejects_unmapped_feature_at_zero_threshold(self) -> None:
        target = SequenceRecord(name="partial_insert", sequence="A" * 20, topology="linear")

        result = handle_search_reference_endpoint(
            "/api/annotation-transfer",
            {
                "reference_records": [
                    {
                        "name": "long_reference",
                        "sequence": "A" * 20 + "C" * 80,
                        "features": [
                            {
                                "key": "misc_feature",
                                "location": "90..100",
                                "qualifiers": {"label": "unmapped tail feature"},
                            }
                        ],
                    }
                ],
                "min_identity_pct": 90.0,
                "min_feature_coverage_pct": 0.0,
                "add_features": True,
            },
            lambda: target,
        )
        assert result is not None
        self.assertEqual(result["transferred_count"], 0)
        self.assertEqual(result["features_added"], 0)
        self.assertEqual(result["references"][0]["rejected_features"], 1)


if __name__ == "__main__":
    unittest.main()
