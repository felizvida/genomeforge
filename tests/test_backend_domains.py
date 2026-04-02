from __future__ import annotations

import tempfile
import uuid
import unittest
from pathlib import Path

import backend.project_api as project_api_module
from backend.analysis_api import handle_analysis_endpoint
from backend.assembly_api import handle_assembly_endpoint
from backend.biology_api import annotation_db_path, enzyme_set_path, handle_biology_endpoint
from backend.core_api import handle_core_endpoint
from backend.design_api import handle_design_endpoint
from backend.project_api import (
    create_share_bundle,
    delete_collection,
    delete_project,
    handle_project_endpoint,
    load_share_bundle,
    project_history_graph,
    render_share_view_html,
    save_collection,
    share_bundle_path,
)
from backend.search_reference_api import blast_local_search, design_sirna_candidates
from backend.trace_api import handle_trace_endpoint
from collab.review import submit_review
from collab.store import get_project_permissions, set_project_permissions
from genomeforge_toolkit import SequenceRecord


class BackendDomainTests(unittest.TestCase):
    def test_blast_local_search_reports_partial_subject_coverage(self) -> None:
        result = blast_local_search(
            query_sequence="ATGGTGAG",
            database_sequences=[{"name": "subject", "sequence": "TTTTATGGTGAGTTTTTTTTTT"}],
            top_hits=5,
            kmer=4,
        )
        self.assertEqual(result["hit_count"], 1)
        hit = result["hits"][0]
        self.assertLess(hit["subject_coverage_pct"], 100.0)
        self.assertGreater(hit["query_coverage_pct"], 0.0)

    def test_blast_local_search_accepts_iupac_query_symbols(self) -> None:
        result = blast_local_search(
            query_sequence="ATGRCC",
            database_sequences=[{"name": "subject", "sequence": "TTTATGGCCTTT"}],
            top_hits=5,
            kmer=4,
        )
        self.assertEqual(result["hit_count"], 1)
        self.assertGreaterEqual(result["hits"][0]["identity_pct"], 100.0)

    def test_trace_endpoint_import_and_summary(self) -> None:
        result = handle_trace_endpoint("/api/import-ab1", {"sequence": "ATGGTGAGCAAG"})
        assert result is not None
        self.assertIn("trace_record", result)
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["length"], 12)

    def test_sirna_candidates_return_ranked_rows(self) -> None:
        result = design_sirna_candidates("ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGC", top_n=5)
        self.assertEqual(len(result["candidates"]), 5)
        self.assertGreaterEqual(result["candidates"][0]["score"], result["candidates"][-1]["score"])

    def test_assembly_endpoint_gibson(self) -> None:
        result = handle_assembly_endpoint(
            "/api/gibson-assemble",
            {
                "fragments": [
                    "ATGCGTACCTGAAAGGTTAC",
                    "GAAAGGTTACCCCTTTAAGG",
                ],
                "min_overlap": 10,
                "circular": False,
            },
        )
        assert result is not None
        self.assertEqual(result["fragment_count"], 2)
        self.assertEqual(result["assembled_length"], len("ATGCGTACCTGAAAGGTTACCCCTTTAAGG"))

    def test_assembly_endpoint_ligation_reports_products(self) -> None:
        result = handle_assembly_endpoint(
            "/api/ligation-sim",
            {
                "vector_sequence": "GAATTCAAAAGGATCC",
                "insert_sequence": "GAATTCTTTTGGATCC",
                "vector_left_enzyme": "EcoRI",
                "vector_right_enzyme": "BamHI",
                "insert_left_enzyme": "BamHI",
                "insert_right_enzyme": "EcoRI",
                "include_byproducts": True,
            },
        )
        assert result is not None
        self.assertTrue(result["products"])
        self.assertIn("predicted_probability", result["products"][0])

    def test_analysis_endpoint_pairwise_and_search(self) -> None:
        record = SequenceRecord(name="Analyze", sequence="ATGGTGAGCAAGGGCGAGGAG", topology="circular")
        result = handle_analysis_endpoint(
            "/api/pairwise-align",
            {"seq_a": "ATGGTGAG", "seq_b": "ATGATGAG", "mode": "dna"},
            lambda: record,
        )
        assert result is not None
        self.assertEqual(result["mode"], "dna")
        self.assertIn("aligned_a", result)

        search = handle_analysis_endpoint(
            "/api/search-entities",
            {"query": "ATGG", "primers": "ATGGTGAG"},
            lambda: record,
        )
        assert search is not None
        self.assertGreaterEqual(search["motif_hit_count"], 1)

    def test_analysis_endpoint_tracks_and_translated_features(self) -> None:
        record = SequenceRecord(name="Trackable", sequence="ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG", topology="linear")
        record.features = [
            type("FeatureLike", (), {"key": "CDS", "location": "1..39", "qualifiers": {"label": "demo_cds", "codon_start": "1"}})()
        ]
        track = handle_analysis_endpoint(
            "/api/sequence-tracks",
            {"start": 1, "end": 39, "frame": 1},
            lambda: record,
        )
        assert track is not None
        self.assertIn("<svg", track["svg"])

        translated = handle_analysis_endpoint(
            "/api/translated-features",
            {"include_slippage": False, "slip_pos_1based": 0},
            lambda: record,
        )
        assert translated is not None
        self.assertEqual(translated["count"], 1)

    def test_biology_endpoint_digest_and_gel(self) -> None:
        record = SequenceRecord(name="Digestible", sequence="AAAAGAATTCTTTTGGATCCAAAA", topology="linear")
        digest = handle_biology_endpoint(
            "/api/digest-advanced",
            {"enzymes": ["EcoRI", "BamHI"], "methylated_motifs": ["GAATTC"]},
            lambda: record,
        )
        assert digest is not None
        self.assertEqual(digest["topology"], "linear")
        self.assertEqual(len(digest["blocked_cuts"]), 1)
        self.assertEqual(digest["blocked_cuts"][0]["enzyme"], "EcoRI")
        self.assertTrue(any(cut["enzyme"] == "BamHI" for cut in digest["cuts"]))

        gel = handle_biology_endpoint(
            "/api/gel-sim",
            {"sizes": [2000, 750, 120], "marker_set": "100bp"},
            lambda: record,
        )
        assert gel is not None
        self.assertEqual(gel["marker_set"], "100bp")
        self.assertEqual(len(gel["sample_bands"]), 3)

    def test_biology_endpoint_features_and_annotation_db(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        db_name = f"backend_annotation_{suffix}"
        set_name = f"backend_enzymes_{suffix}"
        record = SequenceRecord(name="Annotated", sequence="TAATACGACTCACTATAGGGAAAGGAGGATGAAA", topology="linear")
        try:
            added = handle_biology_endpoint(
                "/api/features-add",
                {"key": "promoter", "location": "1..20", "qualifiers": {"label": "T7"}},
                lambda: record,
            )
            assert added is not None
            self.assertEqual(added["count"], 1)

            updated = handle_biology_endpoint(
                "/api/features-update",
                {"index": 0, "key": "promoter", "location": "1..21", "qualifiers": {"label": "T7 updated"}},
                lambda: record,
            )
            assert updated is not None
            self.assertEqual(updated["features"][0]["qualifiers"]["label"], "T7 updated")

            deleted = handle_biology_endpoint("/api/features-delete", {"index": 0}, lambda: record)
            assert deleted is not None
            self.assertEqual(deleted["count"], 0)

            saved_db = handle_biology_endpoint(
                "/api/annot-db-save",
                {
                    "db_name": db_name,
                    "signatures": [
                        {"label": "T7 promoter", "type": "promoter", "motif": "TAATACGACTCACTATAGGG"},
                        {"label": "RBS", "type": "rbs", "motif": "AGGAGG"},
                    ],
                },
                lambda: record,
            )
            assert saved_db is not None
            self.assertTrue(saved_db["saved"])

            applied = handle_biology_endpoint("/api/annot-db-apply", {"db_name": db_name}, lambda: record)
            assert applied is not None
            self.assertGreaterEqual(applied["count"], 2)

            saved_set = handle_biology_endpoint(
                "/api/enzyme-set-save",
                {"set_name": set_name, "enzymes": ["EcoRI", "BamHI"]},
                lambda: record,
            )
            assert saved_set is not None
            self.assertTrue(saved_set["saved"])

            loaded_set = handle_biology_endpoint("/api/enzyme-set-load", {"set_name": set_name}, lambda: record)
            assert loaded_set is not None
            self.assertEqual(sorted(loaded_set["enzymes"]), ["BamHI", "EcoRI"])
        finally:
            annot_path = annotation_db_path(db_name)
            if annot_path.exists():
                annot_path.unlink()
            set_path = enzyme_set_path(set_name)
            if set_path.exists():
                set_path.unlink()

    def test_core_endpoint_record_io_and_sequence_edit(self) -> None:
        record = SequenceRecord(name="RoundTrip", sequence="ATGGTGAGCAAG", topology="circular")
        with tempfile.TemporaryDirectory() as tmpdir:
            export = handle_core_endpoint(
                "/api/export-dna",
                {"name": record.name, "content": f">{record.name}\n{record.sequence}", "topology": record.topology},
                lambda: record,
                Path(tmpdir),
            )
            assert export is not None
            self.assertIn("dna_base64", export)

            imported = handle_core_endpoint(
                "/api/import-dna",
                {"dna_base64": export["dna_base64"]},
                lambda: record,
                Path(tmpdir),
            )
            assert imported is not None
            self.assertEqual(imported["name"], record.name)
            self.assertEqual(imported["length"], record.length)

            edited = handle_core_endpoint(
                "/api/sequence-edit",
                {"op": "insert", "start": 4, "value": "AAA"},
                lambda: record,
                Path(tmpdir),
            )
            assert edited is not None
            self.assertEqual(edited["length"], record.length + 3)
            self.assertIn("AAA", edited["sequence"])

    def test_core_endpoint_batch_digest_and_workspace(self) -> None:
        record = SequenceRecord(name="Core", sequence="AAAAGAATTCTTTTGGATCCAAAA", topology="linear")
        with tempfile.TemporaryDirectory() as tmpdir:
            batch = handle_core_endpoint(
                "/api/batch-digest",
                {
                    "enzymes": ["EcoRI", "BamHI"],
                    "records": [
                        {"name": "rec1", "content": "AAAAGAATTCTTTT", "topology": "linear"},
                        {"name": "rec2", "content": "AAAAGGATCCAAAA", "topology": "linear"},
                    ],
                },
                lambda: record,
                Path(tmpdir),
            )
            assert batch is not None
            self.assertEqual(batch["count"], 2)
            self.assertTrue(all("fragments_bp" in row for row in batch["results"]))

            workspace = handle_core_endpoint(
                "/api/workspace-create",
                {"workspace_name": "backend_domain_ws", "owner": "owner1", "members": ["member1", "member2"]},
                lambda: record,
                Path(tmpdir),
            )
            assert workspace is not None
            self.assertTrue(workspace["created"])
            self.assertIn("owner1", workspace["workspace"]["members"])

    def test_design_endpoint_primer_and_crispr_workflows(self) -> None:
        record = SequenceRecord(
            name="Designable",
            sequence="ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAGTTCAGC",
            topology="linear",
        )
        specificity = handle_design_endpoint(
            "/api/primer-specificity",
            {"forward": "ATGGTGAGCAAG", "reverse": "GAACTTGTGGCC"},
            lambda: record,
        )
        assert specificity is not None
        self.assertEqual(specificity["background_count"], 1)
        self.assertIn("specificity_risk_score", specificity)

        grna = handle_design_endpoint("/api/grna-design", {"pam": "NGG", "spacer_len": 20}, lambda: record)
        assert grna is not None
        self.assertGreater(grna["count"], 0)

        guide = grna["candidates"][0]["guide"]
        offtarget = handle_design_endpoint("/api/crispr-offtarget", {"guide": guide}, lambda: record)
        assert offtarget is not None
        self.assertGreaterEqual(offtarget["hit_count"], 1)

        hdr = handle_design_endpoint(
            "/api/hdr-template",
            {"edit_start_1based": 10, "edit_end_1based": 12, "edit_sequence": "AAA", "left_arm_bp": 20, "right_arm_bp": 20},
            lambda: record,
        )
        assert hdr is not None
        self.assertEqual(hdr["edit_length"], 3)
        self.assertGreater(hdr["donor_length"], 3)

    def test_design_endpoint_primer_specificity_accepts_iupac_symbols(self) -> None:
        record = SequenceRecord(name="IUPACSpecificity", sequence="ATGRCCAAAATCGTTCAAAAGGTT", topology="linear")
        specificity = handle_design_endpoint(
            "/api/primer-specificity",
            {"forward": "ATGGCCAAAATC", "reverse": "AACCTTTTGAAC", "min_amplicon_bp": 20},
            lambda: record,
        )
        assert specificity is not None
        self.assertEqual(specificity["total_predicted_products"], 1)
        self.assertEqual(specificity["reports"][0]["perfect_products"], 1)

    def test_project_endpoint_save_load_and_history(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        project_name = f"backend_domain_project_{suffix}"
        payload = {
            "project_name": project_name,
            "name": "BackendDomain",
            "content": ">BackendDomain\nATGGTGAGCAAGGGCGAGGAG",
            "topology": "circular",
            "history": ["ATGGTGAGCAAG", "ATGGTGAGCAAGGGCGAGGAG"],
        }
        get_record = lambda: SequenceRecord(name="BackendDomain", sequence="ATGGTGAGCAAGGGCGAGGAG", topology="circular")
        try:
            saved = handle_project_endpoint("/api/project-save", payload, get_record)
            assert saved is not None
            self.assertTrue(saved["saved"])

            loaded = handle_project_endpoint("/api/project-load", {"project_name": project_name}, get_record)
            assert loaded is not None
            self.assertEqual(loaded["project_name"], project_name)
            self.assertIn("canonical_record", loaded)

            history = project_history_graph(project_name)
            self.assertEqual(history["node_count"], 2)
            self.assertEqual(len(history["edges"]), 1)
        finally:
            try:
                delete_project(project_name)
            except Exception:
                pass

    def test_share_bundle_render_html(self) -> None:
        suffix = uuid.uuid4().hex[:8]
        project_name = f"backend_share_project_{suffix}"
        collection_name = f"backend_share_collection_{suffix}"
        payload = {
            "project_name": project_name,
            "name": "Shareable",
            "content": ">Shareable\nATGGTGAGCAAGGGCGAGGAGCTGTTCACCGG",
            "topology": "linear",
        }
        get_record = lambda: SequenceRecord(
            name="Shareable",
            sequence="ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGG",
            topology="linear",
        )
        share_path: Path | None = None
        try:
            saved = handle_project_endpoint("/api/project-save", payload, get_record)
            assert saved is not None
            self.assertTrue(saved["saved"])
            save_collection(collection_name, [project_name], notes="backend test")

            share = create_share_bundle([], collection_name=collection_name, include_content=True)
            share_path = share_bundle_path(share["share_id"])
            self.assertTrue(share_path.exists())

            loaded_share = load_share_bundle(share["share_id"])
            self.assertEqual(loaded_share["project_count"], 1)

            html = render_share_view_html(share["share_id"])
            self.assertIn(project_name, html)
            self.assertIn("Shared Bundle", html)
        finally:
            if share_path and share_path.exists():
                share_path.unlink()
            try:
                delete_collection(collection_name)
            except Exception:
                pass
            try:
                delete_project(project_name)
            except Exception:
                pass

    def test_project_permissions_merge_incoming_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = set_project_permissions(root, "merge_project", {"alice": "owner"})
            self.assertTrue(first["saved"])
            second = set_project_permissions(root, "merge_project", {"bob": "reviewer"})
            self.assertTrue(second["saved"])
            roles = get_project_permissions(root, "merge_project")["roles"]
            self.assertEqual(roles["alice"], "owner")
            self.assertEqual(roles["bob"], "reviewer")

    def test_review_approve_uses_review_project_for_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            old_collab_root = project_api_module.COLLAB_ROOT
            project_api_module.COLLAB_ROOT = temp_root
            try:
                set_project_permissions(temp_root, "review_project", {"reviewer_user": "reviewer"})
                review = submit_review(temp_root, "review_project", "editor_user", "ready")
                rid = review["review"]["review_id"]

                approved = handle_project_endpoint(
                    "/api/review-approve",
                    {"review_id": rid, "reviewer": "reviewer_user", "note": "approved without payload project"},
                    lambda: SequenceRecord(name="unused", sequence="ATGC"),
                )
                assert approved is not None
                self.assertTrue(approved["approved"])
                self.assertEqual(approved["review"]["approved_by"], "reviewer_user")
            finally:
                project_api_module.COLLAB_ROOT = old_collab_root

    def test_review_approve_without_permission_is_blocked_even_without_project_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            old_collab_root = project_api_module.COLLAB_ROOT
            project_api_module.COLLAB_ROOT = temp_root
            try:
                set_project_permissions(temp_root, "review_project", {"other_user": "reviewer"})
                review = submit_review(temp_root, "review_project", "editor_user", "ready")
                rid = review["review"]["review_id"]

                with self.assertRaisesRegex(ValueError, "reviewer lacks permission"):
                    handle_project_endpoint(
                        "/api/review-approve",
                        {"review_id": rid, "reviewer": "intruder_user", "note": "should fail"},
                        lambda: SequenceRecord(name="unused", sequence="ATGC"),
                    )
            finally:
                project_api_module.COLLAB_ROOT = old_collab_root


if __name__ == "__main__":
    unittest.main()
