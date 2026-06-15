from __future__ import annotations

import unittest

from backend.compatibility_api import handle_compatibility_endpoint
from compat.interop_audit import compatibility_audit, golden_project_compatibility_report, golden_project_records
from compat.sbol_format import parse_sbol, to_sbol
from genomeforge_toolkit import Feature, SequenceRecord, parse_genbank, to_genbank


class InteropCompatibilityTests(unittest.TestCase):
    def rich_plasmid(self) -> SequenceRecord:
        sequence = "TTGACAGGAGGGAATTCATGGCCGAACTGTAACTCGAGGCTAGC"
        return SequenceRecord(
            name="pInterop_EGFP_demo",
            sequence=sequence,
            topology="circular",
            features=[
                Feature("promoter", "1..6", {"label": "lac promoter", "note": "inducible promoter"}),
                Feature("misc_feature", "13..18", {"label": "EcoRI site", "note": "cloning junction"}),
                Feature("CDS", "19..33", {"label": "mini CDS", "gene": "demo", "codon_start": "1", "product": "MAEL*"}),
                Feature("terminator", "40..48", {"label": "synthetic terminator"}),
                Feature("primer_bind", "19..38", {"label": "seq primer F"}),
            ],
        )

    def test_genbank_round_trip_is_export_safe_for_rich_plasmid(self) -> None:
        plasmid = self.rich_plasmid()
        genbank = to_genbank(plasmid)
        parsed = parse_genbank(genbank)
        report = compatibility_audit(
            {
                "records": [
                    {
                        "name": parsed.name,
                        "topology": parsed.topology,
                        "content": parsed.sequence,
                        "features": [
                            {"key": f.key, "location": f.location, "qualifiers": dict(f.qualifiers)}
                            for f in parsed.features
                        ],
                    }
                ],
                "target_formats": ["genbank"],
            },
            lambda: parsed,
        )
        self.assertEqual(report["status"], "export_safe")
        rt = report["records"][0]["round_trips"][0]
        self.assertTrue(rt["checks"]["features_survive"])
        self.assertTrue(rt["checks"]["qualifiers_preserved"])
        self.assertTrue(rt["checks"]["translations_match"])

    def test_fasta_round_trip_reports_annotation_and_topology_loss(self) -> None:
        plasmid = self.rich_plasmid()
        report = compatibility_audit(
            {
                "records": [
                    {
                        "name": plasmid.name,
                        "topology": plasmid.topology,
                        "content": plasmid.sequence,
                        "features": [
                            {"key": f.key, "location": f.location, "qualifiers": dict(f.qualifiers)}
                            for f in plasmid.features
                        ],
                    }
                ],
                "target_formats": ["fasta"],
            },
            lambda: plasmid,
        )
        rt = report["records"][0]["round_trips"][0]
        self.assertEqual(rt["status"], "needs_review")
        self.assertFalse(rt["checks"]["features_survive"])
        self.assertFalse(rt["checks"]["topology_preserved"])
        self.assertGreater(rt["missing_feature_count"], 0)
        self.assertIn("FASTA preserves sequence", rt["warnings"][0])

    def test_sbol_subset_round_trip_preserves_features_qualifiers_and_topology(self) -> None:
        plasmid = self.rich_plasmid()
        sbol = to_sbol(plasmid)
        parsed = parse_sbol(sbol)
        self.assertEqual(parsed.sequence, plasmid.sequence)
        self.assertEqual(parsed.topology, "circular")
        self.assertEqual(len(parsed.features), len(plasmid.features))
        self.assertEqual(parsed.features[2].qualifiers["product"], "MAEL*")

        report = compatibility_audit(
            {"records": [{"content": sbol, "format": "sbol"}], "target_formats": ["sbol"]},
            lambda: parsed,
        )
        rt = report["records"][0]["round_trips"][0]
        self.assertTrue(rt["export_safe"])
        self.assertTrue(rt["checks"]["qualifiers_preserved"])

    def test_portable_dna_container_round_trip_is_export_safe(self) -> None:
        plasmid = self.rich_plasmid()
        report = compatibility_audit(
            {
                "records": [
                    {
                        "name": plasmid.name,
                        "topology": plasmid.topology,
                        "content": plasmid.sequence,
                        "features": [
                            {"key": f.key, "location": f.location, "qualifiers": dict(f.qualifiers)}
                            for f in plasmid.features
                        ],
                    }
                ],
                "target_formats": ["genomeforge_dna"],
            },
            lambda: plasmid,
        )
        rt = report["records"][0]["round_trips"][0]
        self.assertTrue(rt["export_safe"])
        self.assertIn("not a proprietary SnapGene", rt["warnings"][0])

    def test_golden_project_report_covers_five_real_world_cases(self) -> None:
        report = golden_project_compatibility_report({"target_formats": ["genbank", "sbol", "genomeforge_dna", "fasta"]})
        self.assertEqual(report["golden_project"]["case_count"], 5)
        self.assertEqual(report["record_count"], 5)
        self.assertEqual(len(report["records"]), 5)
        self.assertGreaterEqual(report["summary"]["records_with_export_safe_path"], 5)
        self.assertGreater(report["summary"]["lost_metadata_count"], 0)

    def test_http_handler_returns_golden_project_compatibility_report(self) -> None:
        first = golden_project_records()[0]
        out = handle_compatibility_endpoint(
            "/api/compatibility-golden-project",
            {"target_formats": ["genbank", "sbol"]},
            lambda: first,
        )
        assert out is not None
        self.assertEqual(out["golden_project"]["case_count"], 5)
        self.assertEqual(out["summary"]["round_trip_count"], 10)


if __name__ == "__main__":
    unittest.main()
