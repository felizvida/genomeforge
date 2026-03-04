#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent


class SmokeRunner:
    def __init__(self, base_url: str, verbose: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        self.results: list[tuple[str, bool, str]] = []
        self.ctx: dict[str, Any] = {}
        self.created: dict[str, str] = {}

    def post(self, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8")
            return r.status, json.loads(body)

    def get(self, path: str) -> tuple[int, str]:
        with urllib.request.urlopen(self.base_url + path, timeout=20) as r:
            return r.status, r.read().decode("utf-8", errors="replace")

    def check(self, name: str, fn: Callable[[], None]) -> None:
        try:
            fn()
            self.results.append((name, True, "ok"))
            if self.verbose:
                print(f"[PASS] {name}")
        except Exception as e:  # noqa: BLE001
            self.results.append((name, False, str(e)))
            if self.verbose:
                print(f"[FAIL] {name}: {e}")

    def summary(self) -> dict[str, Any]:
        passed = sum(1 for _, ok, _ in self.results if ok)
        failed = [(n, m) for n, ok, m in self.results if not ok]
        return {
            "total_tests": len(self.results),
            "passed": passed,
            "failed": len(failed),
            "failures": failed,
        }


def wait_until_ready(base_url: str, timeout_s: float = 10.0) -> None:
    start = time.time()
    last_err = None
    while time.time() - start < timeout_s:
        try:
            with urllib.request.urlopen(base_url + "/", timeout=2) as r:
                if r.status == 200:
                    return
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(0.2)
    raise RuntimeError(f"Server did not become ready in {timeout_s}s: {last_err}")


def run_suite(base_url: str, verbose: bool) -> dict[str, Any]:
    r = SmokeRunner(base_url=base_url, verbose=verbose)
    suffix = uuid.uuid4().hex[:8]
    r.created["project"] = f"t_proj_{suffix}"
    r.created["collection"] = f"t_col_{suffix}"
    r.created["annot_db"] = f"t_db_{suffix}"
    r.created["enzyme_set"] = f"t_set_{suffix}"

    seq = "GAATTCCGGATCCATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAGAAGCTTTCTAGA"
    base_payload = {
        "name": "pDemo",
        "topology": "circular",
        "content": seq,
        "features": [
            {"key": "CDS", "location": "13..60", "qualifiers": {"label": "cds1", "codon_start": "1"}},
            {"key": "gene", "location": "5..25", "qualifiers": {"label": "g1"}},
        ],
    }

    # Core
    r.check("api_info", lambda: r.post("/api/info", base_payload)[1]["length"] > 0)
    r.check("api_translate", lambda: len(r.post("/api/translate", {**base_payload, "frame": 1})[1]["protein"]) > 0)
    r.check(
        "api_translated_features",
        lambda: "translated_features"
        in r.post(
            "/api/translated-features",
            {**base_payload, "include_slippage": True, "slip_pos_1based": 20, "slip_type": "-1"},
        )[1],
    )
    r.check("api_digest", lambda: "fragments_bp" in r.post("/api/digest", {**base_payload, "enzymes": "EcoRI,BamHI"})[1])
    r.check(
        "api_digest_advanced",
        lambda: "blocked_cuts"
        in r.post("/api/digest-advanced", {**base_payload, "enzymes": "EcoRI", "methylated_motifs": "GAATTC"})[1],
    )
    r.check(
        "api_star_activity",
        lambda: "star_hit_count"
        in r.post(
            "/api/star-activity-scan",
            {**base_payload, "enzymes": "EcoRI,BamHI", "star_activity_level": 0.8, "include_star_cuts": True},
        )[1],
    )
    r.check(
        "api_canonicalize_record",
        lambda: "canonical_record" in r.post("/api/canonicalize-record", base_payload)[1],
    )

    def _convert_record_roundtrip() -> None:
        c = r.post("/api/canonicalize-record", base_payload)[1]["canonical_record"]
        f = r.post("/api/convert-record", {"canonical_record": c, "target_format": "fasta"})[1]
        g = r.post("/api/convert-record", {"canonical_record": c, "target_format": "genbank"})[1]
        p = r.post("/api/convert-record", {"canonical_record": c, "target_format": "payload"})[1]
        assert f["target_format"] == "fasta" and f["content"].startswith(">")
        assert g["target_format"] == "genbank" and g["content"].lstrip().startswith("LOCUS")
        assert p["target_format"] == "payload" and isinstance(p["payload"], dict)

    r.check("api_convert_record_roundtrip", _convert_record_roundtrip)

    def _dna_export_import() -> None:
        ex = r.post("/api/export-dna", base_payload)[1]
        blob = ex["dna_base64"]
        imp = r.post("/api/import-dna", {"dna_base64": blob})[1]
        assert imp["length"] == len(seq)
        assert imp["topology"] == "circular"
        canonical = imp["canonical_record"]
        jblob = base64.b64encode(json.dumps({"canonical_record": canonical}).encode("utf-8")).decode("ascii")
        imp2 = r.post("/api/import-dna", {"dna_base64": jblob})[1]
        assert imp2["length"] == len(seq)

    r.check("api_dna_export_import", _dna_export_import)

    def _trace_suite() -> None:
        t = r.post("/api/import-ab1", {"sequence": seq})[1]["trace_record"]
        tid = t["trace_id"]
        s = r.post("/api/trace-summary", {"trace_id": tid})[1]["summary"]
        assert s["length"] == len(seq)
        a = r.post("/api/trace-align", {"trace_id": tid, "reference_sequence": seq})[1]
        assert "identity_pct" in a
        e = r.post("/api/trace-edit-base", {"trace_id": tid, "position_1based": 1, "new_base": "T", "quality": 40})[1]
        assert e["trace_record"]["sequence"].startswith("T")
        c = r.post("/api/trace-consensus", {"trace_id": tid, "min_quality": 20})[1]
        assert c["length"] == len(seq)

    r.check("api_trace_suite", _trace_suite)

    def _primers() -> None:
        d = r.post("/api/primers", {**base_payload, "target_start": 12, "target_end": 48, "window": 80})[1]
        r.ctx["fwd"] = d["forward"]["sequence"]
        r.ctx["rev"] = d["reverse"]["sequence"]

    r.check("api_primers", _primers)
    r.check(
        "api_primer_diagnostics",
        lambda: "pair"
        in r.post(
            "/api/primer-diagnostics",
            {"forward": r.ctx.get("fwd", "ATGGCCATTGTAATGGGCCG"), "reverse": r.ctx.get("rev", "TCTAGAAGCTTCTATCGGGC")},
        )[1],
    )
    r.check(
        "api_pcr",
        lambda: "products"
        in r.post("/api/pcr", {**base_payload, "forward": r.ctx.get("fwd"), "reverse": r.ctx.get("rev")})[1],
    )
    r.check(
        "api_primer_specificity",
        lambda: "specificity_risk_score"
        in r.post(
            "/api/primer-specificity",
            {
                **base_payload,
                "forward": r.ctx.get("fwd"),
                "reverse": r.ctx.get("rev"),
                "background_sequences": [{"name": "bg1", "sequence": seq}],
                "max_mismatch": 1,
            },
        )[1],
    )
    r.check(
        "api_primer_rank",
        lambda: "ranked_pairs"
        in r.post(
            "/api/primer-rank",
            {
                "candidates": [
                    {"forward": r.ctx.get("fwd"), "reverse": r.ctx.get("rev")},
                    {"forward": "ATGGCCATTGTAATGGGCCG", "reverse": "TCTAGAAGCTTCTATCGGGC"},
                ],
                "background_sequences": [{"name": "bg1", "sequence": seq}],
                "max_mismatch": 1,
            },
        )[1],
    )
    r.check("api_codon_optimize", lambda: isinstance(r.post("/api/codon-optimize", {**base_payload, "host": "ecoli"})[1], dict))
    r.check(
        "api_grna_design",
        lambda: "candidates"
        in r.post(
            "/api/grna-design",
            {"sequence": seq * 2 + "GGG", "pam": "NGG", "spacer_len": 20, "max_candidates": 20},
        )[1],
    )
    r.check(
        "api_crispr_offtarget",
        lambda: "offtarget_risk_score"
        in r.post(
            "/api/crispr-offtarget",
            {"guide": "ATGGCCATTGTAATGGGCCG", "background_sequences": [{"name": "bg1", "sequence": seq * 2}], "max_mismatch": 3},
        )[1],
    )
    r.check(
        "api_hdr_template",
        lambda: "donor_sequence"
        in r.post(
            "/api/hdr-template",
            {"sequence": seq * 2, "edit_start_1based": 10, "edit_end_1based": 12, "edit_sequence": "GCC", "left_arm_bp": 40, "right_arm_bp": 40},
        )[1],
    )
    r.check("api_map", lambda: "<svg" in r.post("/api/map", {**base_payload, "enzymes": "EcoRI,BamHI"})[1]["svg"])
    r.check(
        "api_sequence_tracks",
        lambda: "<svg" in r.post("/api/sequence-tracks", {**base_payload, "start": 1, "end": 60, "frame": 1})[1]["svg"],
    )
    r.check("api_orfs", lambda: "orfs" in r.post("/api/orfs", {**base_payload, "min_aa": 10})[1])

    # Annotation / feature
    r.check("api_annotate_auto", lambda: "annotations" in r.post("/api/annotate-auto", base_payload)[1])
    r.check(
        "api_annot_db_save",
        lambda: r.post(
            "/api/annot-db-save",
            {"db_name": r.created["annot_db"], "signatures": [{"label": "sig", "type": "gene", "motif": "ATGGCC"}]},
        )[1].get("saved")
        is True,
    )
    r.check("api_annot_db_list", lambda: "databases" in r.post("/api/annot-db-list", {})[1])
    r.check("api_annot_db_load", lambda: "signatures" in r.post("/api/annot-db-load", {"db_name": r.created["annot_db"]})[1])
    r.check(
        "api_annot_db_apply",
        lambda: "annotations" in r.post("/api/annot-db-apply", {**base_payload, "db_name": r.created["annot_db"]})[1],
    )
    r.check("api_features_list", lambda: "features" in r.post("/api/features-list", base_payload)[1])
    r.check(
        "api_features_add",
        lambda: r.post(
            "/api/features-add", {**base_payload, "key": "misc_feature", "location": "2..8", "qualifiers": {"label": "x"}}
        )[1]["count"]
        >= 1,
    )
    r.check(
        "api_features_update",
        lambda: r.post(
            "/api/features-update",
            {**base_payload, "index": 0, "key": "gene", "location": "4..12", "qualifiers": {"label": "upd"}},
        )[1]["count"]
        >= 1,
    )
    r.check("api_features_delete", lambda: r.post("/api/features-delete", {**base_payload, "index": 0})[1]["count"] >= 0)

    # Search/enzyme/edit
    r.check("api_motif", lambda: "positions_1based" in r.post("/api/motif", {**base_payload, "motif": "GAATTC"})[1])
    r.check("api_enzyme_scan", lambda: "enzymes" in r.post("/api/enzyme-scan", base_payload)[1])
    r.check("api_enzyme_info", lambda: "enzymes" in r.post("/api/enzyme-info", {"enzymes": "EcoRI,BamHI"})[1])
    r.check("api_enzyme_set_predefined", lambda: r.post("/api/enzyme-set-predefined", {})[1]["count"] >= 1)
    r.check(
        "api_enzyme_set_save",
        lambda: r.post("/api/enzyme-set-save", {"set_name": r.created["enzyme_set"], "enzymes": "EcoRI,BamHI"})[1].get("saved")
        is True,
    )
    r.check("api_enzyme_set_list", lambda: "sets" in r.post("/api/enzyme-set-list", {})[1])
    r.check("api_enzyme_set_load", lambda: "enzymes" in r.post("/api/enzyme-set-load", {"set_name": r.created["enzyme_set"]})[1])
    r.check(
        "api_enzyme_set_delete",
        lambda: r.post("/api/enzyme-set-delete", {"set_name": r.created["enzyme_set"]})[1].get("deleted") is True,
    )
    r.check(
        "api_sequence_edit",
        lambda: "sequence" in r.post("/api/sequence-edit", {**base_payload, "op": "replace", "start": 1, "end": 3, "value": "ATG"})[1],
    )
    r.check("api_reverse_translate", lambda: r.post("/api/reverse-translate", {"protein": "MSTNPK", "host": "ecoli"})[1]["length"] > 0)
    r.check("api_pairwise_dna", lambda: r.post("/api/pairwise-align", {"seq_a": "GAATTC", "seq_b": "GAATAC", "mode": "dna"})[1]["mode"] == "dna")
    r.check(
        "api_pairwise_protein",
        lambda: r.post("/api/pairwise-align", {"seq_a": "MSTNPK", "seq_b": "MSANPK", "mode": "protein"})[1]["mode"] == "protein",
    )
    r.check("api_multi_align", lambda: "pairwise_to_reference" in r.post("/api/multi-align", {"sequences": ["GAATTC", "GAATAC", "GAATCC"]})[1])
    r.check(
        "api_contig_assemble",
        lambda: "contigs"
        in r.post(
            "/api/contig-assemble",
            {"reads": ["AAACCCGGGTTTATGCATGC", "ATGCATGCGGGAAATTTCCC", "TTTCCCGGGAAATTT"], "min_overlap": 8},
        )[1],
    )

    def _msa() -> None:
        d = r.post(
            "/api/msa",
            {"sequences": ["GAATTCCGGATCCATGGCC", "GAATACCGGATCCATGGCC", "GAATTCCGGTTCCATGGCC"], "method": "progressive"},
        )[1]
        r.ctx["msa"] = d["alignment"]

    r.check("api_msa", _msa)
    r.check("api_alignment_consensus", lambda: "consensus" in r.post("/api/alignment-consensus", {"alignment": r.ctx["msa"]})[1])
    r.check("api_alignment_heatmap_svg", lambda: "<svg" in r.post("/api/alignment-heatmap-svg", {"alignment": r.ctx["msa"]})[1]["svg"])
    r.check("api_phylo_tree", lambda: "newick" in r.post("/api/phylo-tree", {"sequences": ["GAATTC", "GAATAC", "GAATCC"]})[1])
    r.check("api_anneal_oligos", lambda: "overlap_bp" in r.post("/api/anneal-oligos", {"forward": "ATGCGTACCGGTTTAA", "reverse": "TTAAACCGGTACGCAT", "min_overlap": 8})[1])
    r.check("api_mutagenesis", lambda: "sequence" in r.post("/api/mutagenesis", {**base_payload, "start": 10, "end": 12, "mutant": "AAA"})[1])
    r.check(
        "api_protein_edit",
        lambda: r.post("/api/protein-edit", {**base_payload, "aa_index_1based": 2, "new_residue": "K", "frame": 1, "host": "ecoli"})[1].get("edited")
        is True,
    )
    r.check(
        "api_translated_feature_edit",
        lambda: r.post(
            "/api/translated-feature-edit",
            {**base_payload, "feature_index": 0, "aa_index_1based": 2, "new_residue": "A", "host": "ecoli"},
        )[1].get("edited")
        is True,
    )
    r.check("api_gel_sim", lambda: "marker_bands" in r.post("/api/gel-sim", {"sizes": "10000,5000,1000", "marker_set": "100bp"})[1])
    r.check("api_gel_marker_sets", lambda: r.post("/api/gel-marker-sets", {})[1]["count"] >= 1)
    r.check(
        "api_pcr_gel_lanes",
        lambda: "lanes"
        in r.post(
            "/api/pcr-gel-lanes",
            {**base_payload, "primer_pairs": [{"forward": r.ctx.get("fwd"), "reverse": r.ctx.get("rev")}], "marker_set": "1kb_plus"},
        )[1],
    )
    r.check(
        "api_cdna_map",
        lambda: "exons"
        in r.post("/api/cdna-map", {"cdna_sequence": "ATGGCCGATAG", "genome_sequence": "TTTATGGCCAAAAGATAGGG", "min_exon_bp": 3, "max_intron_bp": 100})[1],
    )
    r.check(
        "api_batch_digest",
        lambda: r.post(
            "/api/batch-digest",
            {
                "records": [
                    {"name": "pA", "topology": "circular", "content": "GAATTCCGGATCCATGGCC"},
                    {"name": "pB", "topology": "linear", "content": "AAGCTTGAATTCTCTAGA"},
                ],
                "enzymes": "EcoRI,BamHI",
            },
        )[1]["count"]
        == 2,
    )
    r.check(
        "api_search_entities",
        lambda: "feature_hits" in r.post("/api/search-entities", {**base_payload, "query": "gene", "primers": r.ctx.get("fwd", "ATG")})[1],
    )

    # Data lifecycle
    r.check(
        "api_project_save",
        lambda: r.post("/api/project-save", {**base_payload, "project_name": r.created["project"], "history": ["a", "b"]})[1].get("saved")
        is True,
    )
    r.check("api_project_load", lambda: r.post("/api/project-load", {"project_name": r.created["project"]})[1].get("project_name") == r.created["project"])
    r.check("api_project_list", lambda: r.post("/api/project-list", {})[1]["count"] >= 1)
    r.check("api_project_history_graph", lambda: "nodes" in r.post("/api/project-history-graph", {"project_name": r.created["project"]})[1])
    r.check("api_project_history_svg", lambda: "<svg" in r.post("/api/project-history-svg", {"project_name": r.created["project"]})[1]["svg"])
    r.check(
        "api_workspace_create",
        lambda: r.post(
            "/api/workspace-create",
            {"workspace_name": "ws_" + suffix, "owner": "owner_user", "members": ["reviewer_user", "editor_user"]},
        )[1].get("created")
        is True,
    )
    r.check(
        "api_project_permissions_set",
        lambda: r.post("/api/project-permissions", {"project_name": r.created["project"], "roles": {"reviewer_user": "reviewer"}})[1].get("saved")
        is True,
    )
    r.check(
        "api_project_permissions_get",
        lambda: "roles" in r.post("/api/project-permissions", {"project_name": r.created["project"]})[1],
    )
    r.check(
        "api_project_audit_log",
        lambda: "events" in r.post("/api/project-audit-log", {"project_name": r.created["project"], "limit": 50})[1],
    )
    r.check(
        "api_project_diff",
        lambda: "sequence_identity_pct"
        in r.post(
            "/api/project-diff",
            {
                "project_a": {**base_payload, "project_name": "A"},
                "project_b": {**base_payload, "project_name": "B", "content": seq + "ATG"},
            },
        )[1],
    )
    r.check(
        "api_review_submit",
        lambda: (
            lambda d: (r.ctx.__setitem__("review_id", d["review"]["review_id"]), True)[1]
        )(r.post("/api/review-submit", {"project_name": r.created["project"], "submitter": "editor_user", "summary": "ready"})[1]),
    )
    r.check(
        "api_review_approve",
        lambda: r.post(
            "/api/review-approve",
            {"review_id": r.ctx.get("review_id"), "project_name": r.created["project"], "reviewer": "reviewer_user", "note": "approved"},
        )[1].get("approved")
        is True,
    )
    r.check(
        "api_collection_save",
        lambda: r.post("/api/collection-save", {"collection_name": r.created["collection"], "projects": r.created["project"]})[1].get("saved")
        is True,
    )
    r.check("api_collection_load", lambda: "projects" in r.post("/api/collection-load", {"collection_name": r.created["collection"]})[1])
    r.check("api_collection_list", lambda: r.post("/api/collection-list", {})[1]["count"] >= 1)
    r.check(
        "api_collection_add_project",
        lambda: r.post("/api/collection-add-project", {"collection_name": r.created["collection"], "project_name": r.created["project"]})[1].get("saved")
        is True,
    )

    def _share() -> None:
        d = r.post("/api/share-create", {"projects": [r.created["project"]], "include_content": True})[1]
        sid = d["share_id"]
        r.ctx["share_id"] = sid
        assert r.post("/api/share-load", {"share_id": sid})[1]["share_id"] == sid
        assert "Shared Bundle" in r.get("/share/" + sid)[1]

    r.check("api_share_create_load_get", _share)
    r.check(
        "api_collection_delete",
        lambda: r.post("/api/collection-delete", {"collection_name": r.created["collection"]})[1].get("deleted") is True,
    )
    r.check(
        "api_project_delete",
        lambda: r.post("/api/project-delete", {"project_name": r.created["project"]})[1].get("deleted") is True,
    )

    # Cloning suite
    r.check(
        "api_gibson_assemble",
        lambda: r.post("/api/gibson-assemble", {"fragments": ["AAACCCGGGTTTATGCATGC", "ATGCATGCGGGAAATTTCCC"], "min_overlap": 8})[1].get("assembled_length", 0) > 0,
    )
    r.check(
        "api_golden_gate",
        lambda: r.post(
            "/api/golden-gate",
            {
                "parts": [
                    {"sequence": "ATGAAA", "left_overhang": "AATG", "right_overhang": "GGCC"},
                    {"sequence": "CCCTTT", "left_overhang": "GGCC", "right_overhang": "TTAA"},
                ],
                "circular": False,
                "enforce_complement": False,
            },
        )[1].get("assembled_length", 0) > 0,
    )
    r.check("api_gateway_cloning", lambda: isinstance(r.post("/api/gateway-cloning", {"entry_clone": "ACAAGTTTGTACAAAAAAGCAGGCTATGAAACCCGGGACCACTTTGTACAAGAAAGCTGGGT", "destination_vector": "GGGCCCAAATTTCCCGGG"})[1], dict))
    r.check("api_topo_cloning", lambda: r.post("/api/topo-cloning", {"vector": "GGGCCCAAATTTCCCGGG", "insert": "ATGAAACCCGGGA", "mode": "TA"})[1].get("product_length", 0) > 0)
    r.check("api_ta_gc_cloning", lambda: r.post("/api/ta-gc-cloning", {"vector": "GGGCCCAAATTTCCCGGG", "insert": "ATGAAACCCGGGA", "mode": "TA"})[1].get("product_length", 0) > 0)
    r.check("api_cloning_compatibility", lambda: "ok" in r.post("/api/cloning-compatibility", {"mode": "restriction", "vector": "GAATTCCGGATCC", "insert": "GAATTCAAAAGGATCC", "enzymes": "EcoRI,BamHI"})[1])
    r.check(
        "api_ligation_sim",
        lambda: "products"
        in r.post(
            "/api/ligation-sim",
            {
                "vector_sequence": "GAATTCCGGATCCATGGCC",
                "insert_sequence": "ATGGCCGGATCCGAATTC",
                "vector_left_enzyme": "EcoRI",
                "vector_right_enzyme": "BamHI",
                "insert_left_enzyme": "BamHI",
                "insert_right_enzyme": "EcoRI",
                "include_byproducts": True,
                "star_activity_level": 0.2,
            },
        )[1],
    )
    r.check("api_in_fusion", lambda: r.post("/api/in-fusion", {"fragments": ["AAACCCGGGTTTATGCATGC", "ATGCATGCGGGAAATTTCCC"], "min_overlap": 8, "circular": False})[1].get("assembled_length", 0) > 0)
    r.check(
        "api_overlap_extension_pcr",
        lambda: r.post("/api/overlap-extension-pcr", {"fragment_a": "AAACCCGGGTTTATGCATGC", "fragment_b": "ATGCATGCGGGAAATTTCCC", "min_overlap": 8})[1].get("product_length", 0) > 0,
    )
    r.check("get_root", lambda: "Genome Forge" in r.get("/")[1])

    return r.summary()


def cleanup_artifacts() -> None:
    for d in ["projects", "collections", "shares", "annotation_db", "enzyme_sets", "collab_data"]:
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run extensive Genome Forge smoke test")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8121)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    server = subprocess.Popen(
        ["python3", "web_ui.py", "--host", args.host, "--port", str(args.port)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_until_ready(base_url, timeout_s=12.0)
        summary = run_suite(base_url=base_url, verbose=args.verbose)
        print(json.dumps(summary, indent=2))
        return 0 if summary["failed"] == 0 else 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:  # noqa: BLE001
            server.kill()
        cleanup_artifacts()


if __name__ == "__main__":
    raise SystemExit(main())
