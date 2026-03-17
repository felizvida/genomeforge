#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent

# Real-world biological sequences (commonly used references in molecular biology)
EGFP_CDS = (
    "ATGGTGAGCAAGGGCGAGGAGCTGTTCACCGGGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAG"
    "TTCAGCGTGTCCGGCGAGGGCGAGGGCGATGCCACCTACGGCAAGCTGACCCTGAAGTTCATCTGCACCACCGGCAAGCTGC"
    "CCGTGCCCTGGCCCACCCTCGTGACCACCCTGACCTACGGCGTGCAGTGCTTCAGCCGCTACCCCGACCACATGAAGCAGCA"
    "CGACTTCTTCAAGTCCGCCATGCCCGAAGGCTACGTCCAGGAGCGCACCATCTTCTTCAAGGACGACGGCAACTACAAGACCC"
    "GCGCCGAGGTGAAGTTCGAGGGCGACACCCTGGTGAACCGCATCGAGCTGAAGGGCATCGACTTCAAGGAGGACGGCAACAT"
    "CCTGGGGCACAAGCTGGAGTACAACTACAACAGCCACAACGTCTATATCATGGCCGACAAGCAGAAGAACGGCATCAAGGTG"
    "AACTTCAAGATCCGCCACAACATCGAGGACGGCAGCGTGCAGCTCGCCGACCACTACCAGCAGAACACCCCCATCGGCGACG"
    "GCCCCGTGCTGCTGCCCGACAACCACTACCTGAGCACCCAGTCCAAGCTGAGCAAAGACCCCAACGAGAAGCGCGATCACAT"
    "GGTCCTGCTGGAGTTCGTGACCGCCGCCGGGATCACTCTCGGCATGGACGAGCTGTACAAGTAA"
)

MCHERRY_CDS = (
    "ATGGTGAGCAAGGGCGAGGAGGATAACATGGCCATCATCAAGGAGTTCATGCGCTTCAAGGTGCACATGGAGGGCTCCGTGA"
    "ACGGCCACGAGTTCGAGATCGAGGGCGAGGGCGAGGGCCGCCCCTACGAGGGCACCCAGACCGCCAAGCTGAAGGTGACCAA"
    "GGGTGGCCCCCTGCCCTTCGCCTGGGACATCCTGTCCCCTCAGTTCATGTACGGCTCCAAGGCCTACGTGAAGCACCCCGCC"
    "GACATCCCCGACTACTTGAAGCTGTCCTTCCCCGAGGGCTTCAAGTGGGAGCGCGTGATGAACTTCGAGGACGGCGGCGTGG"
    "TGACCGTGACCCAGGACTCCTCCCTGCAGGACGGCGAGTTCATCTACAAGGTGAAGCTGCGCGGCACCAACTTCCCCTCCGA"
    "CGGCCCCGTAATGCAGAAGAAGACCATGGGCTGGGAGGCCTCCTCCGAGCGGATGTACCCCGAGGACGGCGCCCTGAAGGGC"
    "GAGATCAAGCAGAGGCTGAAGCTGAAGGACGGCGGCCACTACGACGCTGAGGTCAAGACCACCTACAAGGCCAAGAAGCCCG"
    "TGCAGCTGCCCGGCGCCTACAACGTCAACATCAAGTTGGACATCACCTCCCACAACGAGGACTACACCATCGTGGAACAGTA"
    "CGAACGCGCCGAGGGCCGCCACTCCACCGGCGGCATGGACGAGCTGTACAAGTAA"
)

# pUC19 multiple cloning site (MCS), used in many cloning protocols
PUC19_MCS = "GAATTCGAGCTCGGTACCCGGGGATCCTCTAGAGTCGACCTGCAGGCATGCAAGCTT"


@dataclass
class StepResult:
    name: str
    objective: str
    status: str
    duration_ms: int
    details: dict[str, Any]
    error: str = ""


class FunctionalRunner:
    def __init__(self, base_url: str, verbose: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        self.steps: list[StepResult] = []
        self.ctx: dict[str, Any] = {}
        self.created: dict[str, str] = {}

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8"))

    def get(self, path: str) -> str:
        with urllib.request.urlopen(self.base_url + path, timeout=25) as r:
            return r.read().decode("utf-8", errors="replace")

    def check(self, name: str, objective: str, fn: Callable[[], dict[str, Any]]) -> None:
        start = time.time()
        try:
            details = summarize_object(fn())
            dur = int((time.time() - start) * 1000)
            self.steps.append(StepResult(name, objective, "PASS", dur, details))
            if self.verbose:
                print(f"[PASS] {name} ({dur} ms)")
        except Exception as e:  # noqa: BLE001
            dur = int((time.time() - start) * 1000)
            self.steps.append(StepResult(name, objective, "FAIL", dur, {}, str(e)))
            if self.verbose:
                print(f"[FAIL] {name} ({dur} ms): {e}")

    def summary(self) -> dict[str, Any]:
        passed = sum(1 for s in self.steps if s.status == "PASS")
        failed = [s for s in self.steps if s.status == "FAIL"]
        return {
            "total_steps": len(self.steps),
            "passed": passed,
            "failed": len(failed),
            "failures": [{"name": s.name, "error": s.error} for s in failed],
        }


def wait_until_ready(base_url: str, timeout_s: float = 12.0) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            with urllib.request.urlopen(base_url + "/", timeout=2) as r:
                if r.status == 200:
                    return
        except Exception:  # noqa: BLE001
            time.sleep(0.2)
    raise RuntimeError(f"Server did not become ready in {timeout_s}s")


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def summarize_object(value: Any, depth: int = 0) -> Any:
    if depth >= 3:
        return f"<{type(value).__name__}>"
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= 8:
                out["..."] = f"+{len(value) - 8} keys"
                break
            if k in {"svg", "sequence", "product_sequence", "assembled_sequence", "aligned_a", "aligned_b"}:
                text = str(v)
                out[k] = f"<{len(text)} chars>"
            elif k in {"numbering", "conservation", "translated_features", "pairwise_to_reference", "products"} and isinstance(v, list):
                out[k] = f"<list:{len(v)}>"
            else:
                out[k] = summarize_object(v, depth + 1)
        return out
    if isinstance(value, list):
        if len(value) > 6:
            preview = [summarize_object(x, depth + 1) for x in value[:3]]
            preview.append(f"... ({len(value) - 3} more)")
            return preview
        return [summarize_object(x, depth + 1) for x in value]
    if isinstance(value, str):
        if len(value) > 180:
            return value[:120] + f"... <{len(value)} chars total>"
        return value
    return value


def run_real_world_suite(base_url: str, verbose: bool) -> tuple[dict[str, Any], list[StepResult]]:
    r = FunctionalRunner(base_url, verbose=verbose)
    suffix = uuid.uuid4().hex[:8]
    r.created["project"] = f"real_proj_{suffix}"
    r.created["collection"] = f"real_col_{suffix}"
    r.created["annot_db"] = f"real_db_{suffix}"
    r.created["enzyme_set"] = f"real_set_{suffix}"
    r.created["reference_db"] = f"real_ref_{suffix}"

    egfp_payload = {
        "name": "EGFP_CDS",
        "topology": "linear",
        "content": f">EGFP\n{EGFP_CDS}",
        "features": [
            {"key": "CDS", "location": f"1..{len(EGFP_CDS)}", "qualifiers": {"label": "EGFP", "codon_start": "1"}},
            {"key": "gene", "location": f"1..{len(EGFP_CDS)}", "qualifiers": {"label": "gfp"}},
        ],
    }
    mcherry_payload = {
        "name": "mCherry_CDS",
        "topology": "linear",
        "content": f">mCherry\n{MCHERRY_CDS}",
        "features": [{"key": "CDS", "location": f"1..{len(MCHERRY_CDS)}", "qualifiers": {"label": "mCherry", "codon_start": "1"}}],
    }
    puc_payload = {
        "name": "pUC19_MCS",
        "topology": "circular",
        "content": f">pUC19_MCS\n{PUC19_MCS}",
        "features": [{"key": "misc_feature", "location": "1..63", "qualifiers": {"label": "MCS"}}],
    }

    r.check("info_egfp", "Compute basic stats for EGFP CDS", lambda: r.post("/api/info", egfp_payload))
    r.check("info_mcherry", "Compute basic stats for mCherry CDS", lambda: r.post("/api/info", mcherry_payload))
    r.check("translate_egfp", "Translate EGFP coding sequence", lambda: r.post("/api/translate", {**egfp_payload, "frame": 1}))
    r.check(
        "translated_features_egfp",
        "Generate translated feature report from EGFP feature annotation",
        lambda: r.post("/api/translated-features", {**egfp_payload, "include_slippage": False, "slip_pos_1based": 0}),
    )
    r.check(
        "digest_puc_mcs",
        "Digest pUC19 MCS region with common restriction enzymes",
        lambda: r.post("/api/digest", {**puc_payload, "enzymes": "EcoRI,BamHI,HindIII,XbaI,PstI,KpnI"}),
    )
    r.check(
        "digest_adv_methyl",
        "Run methylation-aware digest on pUC19 MCS",
        lambda: r.post(
            "/api/digest-advanced",
            {**puc_payload, "enzymes": "EcoRI,BamHI,HindIII", "methylated_motifs": "GAATTC,GGATCC"},
        ),
    )
    r.check(
        "star_activity_scan",
        "Scan star activity risk on restriction panel",
        lambda: r.post(
            "/api/star-activity-scan",
            {**puc_payload, "enzymes": "EcoRI,BamHI,HindIII", "star_activity_level": 0.65, "include_star_cuts": True},
        ),
    )
    r.check("map_svg", "Render plasmid/linear map SVG", lambda: r.post("/api/map", {**puc_payload, "enzymes": "EcoRI,BamHI,HindIII"}))
    r.check(
        "sequence_track_svg",
        "Render sequence track for coding region",
        lambda: r.post("/api/sequence-tracks", {**egfp_payload, "start": 1, "end": 180, "frame": 1}),
    )
    r.check(
        "sequence_analytics_svg",
        "Render multi-track sequence analytics lens (GC/skew/complexity/stop-density)",
        lambda: r.post("/api/sequence-analytics-svg", {**egfp_payload, "start": 1, "end": 720, "window": 120, "step": 20}),
    )
    r.check(
        "comparison_lens_svg",
        "Render comparison lens for divergence hotspots between EGFP and mCherry segments",
        lambda: r.post(
            "/api/comparison-lens-svg",
            {"seq_a": EGFP_CDS[:900], "seq_b": MCHERRY_CDS[:900], "window": 60},
        ),
    )
    r.check("motif_search", "Find canonical EcoRI motif in pUC19 MCS", lambda: r.post("/api/motif", {**puc_payload, "motif": "GAATTC"}))
    r.check("orf_scan", "Find ORFs in EGFP sequence", lambda: r.post("/api/orfs", {**egfp_payload, "min_aa": 60}))

    def _primer_design() -> dict[str, Any]:
        d = r.post("/api/primers", {**egfp_payload, "target_start": 60, "target_end": 520, "window": 140})
        r.ctx["fwd"] = d["forward"]["sequence"]
        r.ctx["rev"] = d["reverse"]["sequence"]
        return {"forward_len": len(r.ctx["fwd"]), "reverse_len": len(r.ctx["rev"])}

    r.check("primer_design", "Design primers for EGFP internal region", _primer_design)
    r.check(
        "primer_diagnostics",
        "Evaluate primer thermodynamics and pair behavior",
        lambda: r.post(
            "/api/primer-diagnostics",
            {"forward": r.ctx["fwd"], "reverse": r.ctx["rev"], "na_mM": 50, "primer_nM": 250},
        ),
    )
    r.check(
        "primer_specificity",
        "Estimate primer specificity against real CDS backgrounds",
        lambda: r.post(
            "/api/primer-specificity",
            {
                "forward": r.ctx["fwd"],
                "reverse": r.ctx["rev"],
                "background_sequences": [
                    {"name": "EGFP", "sequence": EGFP_CDS},
                    {"name": "mCherry", "sequence": MCHERRY_CDS},
                ],
                "max_mismatch": 1,
            },
        ),
    )
    r.check(
        "primer_rank",
        "Rank competing primer pairs by specificity risk",
        lambda: r.post(
            "/api/primer-rank",
            {
                "candidates": [
                    {"forward": r.ctx["fwd"], "reverse": r.ctx["rev"]},
                    {"forward": EGFP_CDS[60:85], "reverse": EGFP_CDS[500:525]},
                ],
                "background_sequences": [
                    {"name": "EGFP", "sequence": EGFP_CDS},
                    {"name": "mCherry", "sequence": MCHERRY_CDS},
                ],
                "max_mismatch": 1,
            },
        ),
    )
    r.check("virtual_pcr", "Simulate PCR amplification using designed EGFP primers", lambda: r.post("/api/pcr", {**egfp_payload, "forward": r.ctx["fwd"], "reverse": r.ctx["rev"]}))
    r.check(
        "pcr_gel_lanes",
        "Simulate gel lanes for designed primer pair",
        lambda: r.post(
            "/api/pcr-gel-lanes",
            {**egfp_payload, "primer_pairs": [{"forward": r.ctx["fwd"], "reverse": r.ctx["rev"]}], "marker_set": "1kb_plus"},
        ),
    )
    r.check(
        "codon_optimize_yeast",
        "Codon-optimize EGFP for yeast host",
        lambda: r.post("/api/codon-optimize", {**egfp_payload, "host": "yeast", "frame": 1}),
    )
    r.check("canonicalize_record", "Convert EGFP record to canonical schema", lambda: r.post("/api/canonicalize-record", egfp_payload))

    def _convert_record() -> dict[str, Any]:
        c = r.post("/api/canonicalize-record", egfp_payload)["canonical_record"]
        f = r.post("/api/convert-record", {"canonical_record": c, "target_format": "fasta"})
        g = r.post("/api/convert-record", {"canonical_record": c, "target_format": "genbank"})
        e = r.post("/api/convert-record", {"canonical_record": c, "target_format": "embl"})
        j = r.post("/api/convert-record", {"canonical_record": c, "target_format": "json"})
        d = r.post("/api/convert-record", {"canonical_record": c, "target_format": "dna"})
        p = r.post("/api/convert-record", {"canonical_record": c, "target_format": "payload"})
        assert f["target_format"] == "fasta"
        assert g["target_format"] == "genbank"
        assert e["target_format"] == "embl"
        assert j["target_format"] == "json"
        assert d["target_format"] == "genomeforge_dna" and int(d["bytes"]) > 0
        assert p["target_format"] == "payload"
        return {
            "fasta_len": len(f["content"]),
            "genbank_len": len(g["content"]),
            "embl_len": len(e["content"]),
            "json_len": len(j["content"]),
            "dna_bytes": int(d["bytes"]),
        }

    r.check("convert_record_roundtrip", "Roundtrip canonical -> FASTA/GenBank/EMBL/JSON/DNA container/payload", _convert_record)
    r.check(
        "dna_export_import",
        "Export and import Genome Forge DNA container",
        lambda: r.post(
            "/api/import-dna",
            {"dna_base64": r.post("/api/export-dna", egfp_payload)["dna_base64"]},
        ),
    )
    r.check(
        "trace_import_align_consensus",
        "Synthetic trace import + align + consensus pipeline",
        lambda: (
            lambda imp: (
                r.post("/api/trace-summary", {"trace_id": imp["trace_record"]["trace_id"]}),
                r.post(
                    "/api/trace-align",
                    {
                        "trace_id": imp["trace_record"]["trace_id"],
                        "reference_sequence": EGFP_CDS,
                    },
                ),
                r.post("/api/trace-consensus", {"trace_id": imp["trace_record"]["trace_id"], "min_quality": 20}),
            )[-1]
        )(r.post("/api/import-ab1", {"sequence": EGFP_CDS})),
    )

    def _trace_chromatogram_svg() -> dict[str, Any]:
        imp = r.post("/api/import-ab1", {"sequence": EGFP_CDS})
        tr = imp["trace_record"]
        positions = [6 * (i + 1) for i in range(len(tr["sequence"]))]
        traces = {base: [0] * (positions[-1] + 6) for base in "ACGT"}
        for idx, pos in enumerate(positions):
            traces[tr["sequence"][idx]][pos - 1] = 1200
        wide = {**tr, "positions": positions, "traces": traces}
        out = r.post("/api/trace-chromatogram-svg", {"trace_record": wide, "start": 1, "end": 120, "max_points": 160})
        assert_condition(int(out["sample_end_index_0based"]) > 120, "expected raw-signal sample coordinates")
        return out

    r.check(
        "trace_chromatogram_svg",
        "Render Sanger chromatogram SVG from synthetic trace",
        _trace_chromatogram_svg,
    )
    r.check(
        "trace_verify_genotyping",
        "Verify trace against reference and genotype selected loci",
        lambda: (
            lambda imp: r.post(
                "/api/trace-verify",
                {
                    "trace_id": imp["trace_record"]["trace_id"],
                    "reference_sequence": EGFP_CDS,
                    "genotype_positions": [10, 20, 30, 40],
                    "expected_bases": {"10": EGFP_CDS[9], "20": EGFP_CDS[19], "30": EGFP_CDS[29]},
                    "identity_threshold_pct": 97.0,
                    "max_mismatches": 10,
                },
            )
        )(r.post("/api/import-ab1", {"sequence": EGFP_CDS})),
    )
    r.check(
        "blast_like_search",
        "Run BLAST-like local similarity search across real sequence panel",
        lambda: (
            lambda out: (
                assert_condition(len(out.get("hits", [])) >= 1, "expected at least one hit"),
                assert_condition(float(out["hits"][0]["subject_coverage_pct"]) < 100.0, "local hit should not cover full subject"),
                out,
            )[-1]
        )(
            r.post(
                "/api/blast-search",
                {
                    "query_sequence": EGFP_CDS[:240],
                    "database_sequences": [
                        {"name": "EGFP", "sequence": EGFP_CDS},
                        {"name": "mCherry", "sequence": MCHERRY_CDS},
                        {"name": "pUC19_MCS", "sequence": PUC19_MCS},
                    ],
                    "kmer": 8,
                    "top_hits": 5,
                },
            )
        ),
    )
    r.check(
        "search_entities",
        "Search across features, enzymes, and primer hits",
        lambda: r.post("/api/search-entities", {**egfp_payload, "query": "gfp", "primers": f"{r.ctx['fwd']},{r.ctx['rev']}"}),
    )
    r.check(
        "reverse_translate",
        "Reverse-translate protein motif into DNA",
        lambda: r.post("/api/reverse-translate", {"protein": "MSTNPKPQRKTK", "host": "ecoli"}),
    )
    r.check(
        "protein_edit",
        "Edit amino acid in EGFP CDS and regenerate nucleotide sequence",
        lambda: r.post("/api/protein-edit", {**egfp_payload, "aa_index_1based": 10, "new_residue": "K", "frame": 1, "host": "ecoli"}),
    )
    r.check(
        "translated_feature_edit",
        "Apply AA edit through translated-feature editor",
        lambda: r.post(
            "/api/translated-feature-edit",
            {**egfp_payload, "feature_index": 0, "aa_index_1based": 20, "new_residue": "A", "host": "ecoli"},
        ),
    )
    r.check("sequence_edit", "Apply nucleotide replacement edit in EGFP", lambda: r.post("/api/sequence-edit", {**egfp_payload, "op": "replace", "start": 10, "end": 15, "value": "GCCGCC"}))
    r.check("mutagenesis", "Apply mutagenesis edit in EGFP region", lambda: r.post("/api/mutagenesis", {**egfp_payload, "start": 40, "end": 45, "mutant": "GAGGAG"}))
    r.check(
        "pairwise_dna",
        "Run pairwise DNA alignment between EGFP and mCherry",
        lambda: r.post("/api/pairwise-align", {"seq_a": EGFP_CDS, "seq_b": MCHERRY_CDS, "mode": "dna"}),
    )

    def _pairwise_protein() -> dict[str, Any]:
        p1 = r.post("/api/translate", {**egfp_payload, "frame": 1, "to_stop": True})["protein"]
        p2 = r.post("/api/translate", {**mcherry_payload, "frame": 1, "to_stop": True})["protein"]
        return r.post("/api/pairwise-align", {"seq_a": p1, "seq_b": p2, "mode": "protein"})

    r.check("pairwise_protein", "Run protein alignment between EGFP and mCherry", _pairwise_protein)
    r.check(
        "grna_design",
        "Design gRNA candidates on EGFP sequence",
        lambda: r.post("/api/grna-design", {"sequence": EGFP_CDS, "pam": "NGG", "spacer_len": 20, "max_candidates": 50}),
    )
    r.check(
        "crispr_offtarget",
        "Scan gRNA off-targets across EGFP and mCherry",
        lambda: r.post(
            "/api/crispr-offtarget",
            {
                "guide": EGFP_CDS[:20],
                "background_sequences": [
                    {"name": "EGFP", "sequence": EGFP_CDS},
                    {"name": "mCherry", "sequence": MCHERRY_CDS},
                ],
                "max_mismatch": 3,
            },
        ),
    )
    r.check(
        "hdr_template",
        "Design HDR donor around targeted edit window",
        lambda: r.post(
            "/api/hdr-template",
            {
                "sequence": EGFP_CDS,
                "edit_start_1based": 100,
                "edit_end_1based": 102,
                "edit_sequence": "GCC",
                "left_arm_bp": 60,
                "right_arm_bp": 60,
            },
        ),
    )
    r.check("multi_align_ref", "Reference-based multiple alignment of real CDS inputs", lambda: r.post("/api/multi-align", {"sequences": [EGFP_CDS, MCHERRY_CDS, EGFP_CDS[:300]]}))

    def _msa_progressive() -> dict[str, Any]:
        d = r.post("/api/msa", {"sequences": [EGFP_CDS, MCHERRY_CDS, EGFP_CDS[:500]], "method": "progressive"})
        r.ctx["msa"] = d["alignment"]
        return {"rows": len(r.ctx["msa"]), "columns": len(r.ctx["msa"][0]) if r.ctx["msa"] else 0}

    r.check("msa_progressive", "Progressive MSA on real coding sequences", _msa_progressive)
    r.check("msa_consensus", "Consensus generation from MSA", lambda: r.post("/api/alignment-consensus", {"alignment": r.ctx["msa"]}))
    r.check("msa_heatmap", "MSA identity heatmap SVG generation", lambda: r.post("/api/alignment-heatmap-svg", {"alignment": r.ctx["msa"]}))
    r.check("phylo_tree", "Generate UPGMA phylogenetic tree from real sequences", lambda: r.post("/api/phylo-tree", {"sequences": [EGFP_CDS, MCHERRY_CDS, EGFP_CDS[:500]]}))
    r.check("anneal_oligos", "Simulate oligo annealing with realistic overhangs", lambda: r.post("/api/anneal-oligos", {"forward": EGFP_CDS[:30], "reverse": EGFP_CDS[10:40], "min_overlap": 12}))
    r.check("gel_sim", "Simulate agarose gel marker + product sizes", lambda: r.post("/api/gel-sim", {"sizes": "720,711,540,300,180", "marker_set": "100bp"}))
    r.check("gel_marker_sets", "List available marker ladder sets", lambda: r.post("/api/gel-marker-sets", {}))
    r.check("annotate_auto", "Auto-annotate EGFP sequence motifs", lambda: r.post("/api/annotate-auto", egfp_payload))
    r.check(
        "annotation_db_save",
        "Save annotation DB with real motif signatures",
        lambda: r.post(
            "/api/annot-db-save",
            {
                "db_name": r.created["annot_db"],
                "signatures": [
                    {"label": "GFP start motif", "type": "gene", "motif": EGFP_CDS[:18]},
                    {"label": "mCherry start motif", "type": "gene", "motif": MCHERRY_CDS[:18]},
                ],
            },
        ),
    )
    r.check("annotation_db_list", "List annotation DB libraries", lambda: r.post("/api/annot-db-list", {}))
    r.check("annotation_db_load", "Load saved annotation DB", lambda: r.post("/api/annot-db-load", {"db_name": r.created["annot_db"]}))
    r.check("annotation_db_apply", "Apply saved annotation DB to EGFP", lambda: r.post("/api/annot-db-apply", {**egfp_payload, "db_name": r.created["annot_db"]}))
    r.check(
        "reference_db_save",
        "Save reusable reference element library for auto-flagging",
        lambda: r.post(
            "/api/reference-db-save",
            {
                "db_name": r.created["reference_db"],
                "elements": [
                    {"label": "EGFP start", "type": "gene", "sequence": EGFP_CDS[:18]},
                    {"label": "mCherry start", "type": "gene", "sequence": MCHERRY_CDS[:18]},
                    {"label": "MCS EcoRI-BamHI", "type": "misc_feature", "sequence": "GAATTCCGGATCC"},
                ],
            },
        ),
    )
    r.check("reference_db_list", "List reference libraries", lambda: r.post("/api/reference-db-list", {}))
    r.check("reference_db_load", "Load reference library", lambda: r.post("/api/reference-db-load", {"db_name": r.created["reference_db"]}))
    r.check(
        "reference_scan_autoflag",
        "Scan sequence against reference library and add feature flags",
        lambda: (
            lambda out: (
                assert_condition(int(out.get("features_added", 0)) >= 1, "expected flagged features"),
                assert_condition(len(out.get("features", [])) >= len(egfp_payload["features"]) + 1, "expected returned feature state"),
                out,
            )[-1]
        )(r.post("/api/reference-scan", {**egfp_payload, "db_name": r.created["reference_db"], "add_features": True})),
    )
    r.check(
        "sirna_design",
        "Design siRNA candidates on EGFP coding region",
        lambda: r.post("/api/sirna-design", {"sequence": EGFP_CDS, "min_len": 19, "max_len": 21, "top_n": 30}),
    )
    r.check(
        "sirna_map",
        "Map an siRNA candidate onto EGFP sequence",
        lambda: r.post("/api/sirna-map", {"sequence": EGFP_CDS, "sirna_sequence": "AUGGUGAGCAAGGGCGAGG"}),
    )
    r.check("features_list", "List feature entries on EGFP record", lambda: r.post("/api/features-list", egfp_payload))
    r.check(
        "features_add_update_delete",
        "Add, update, and delete a feature entry",
        lambda: (
            r.post("/api/features-add", {**egfp_payload, "key": "promoter", "location": "1..30", "qualifiers": {"label": "CMV_like"}}),
            r.post("/api/features-update", {**egfp_payload, "index": 0, "key": "CDS", "location": "1..720", "qualifiers": {"label": "EGFP_mod"}}),
            r.post("/api/features-delete", {**egfp_payload, "index": 0}),
        )[-1],
    )
    r.check("enzyme_scan", "Scan built-in enzymes against real sequence", lambda: r.post("/api/enzyme-scan", egfp_payload))
    r.check("enzyme_info", "Fetch metadata for common restriction enzymes", lambda: r.post("/api/enzyme-info", {"enzymes": "EcoRI,BamHI,HindIII"}))
    r.check("enzyme_set_predefined", "Enumerate predefined enzyme sets", lambda: r.post("/api/enzyme-set-predefined", {}))
    r.check("enzyme_set_save", "Save custom enzyme panel", lambda: r.post("/api/enzyme-set-save", {"set_name": r.created["enzyme_set"], "enzymes": "EcoRI,BamHI,HindIII"}))
    r.check("enzyme_set_list", "List custom enzyme panels", lambda: r.post("/api/enzyme-set-list", {}))
    r.check("enzyme_set_load", "Load custom enzyme panel", lambda: r.post("/api/enzyme-set-load", {"set_name": r.created["enzyme_set"]}))
    r.check("enzyme_set_delete", "Delete custom enzyme panel", lambda: r.post("/api/enzyme-set-delete", {"set_name": r.created["enzyme_set"]}))

    r.check(
        "batch_digest",
        "Run batch digest across multiple real records",
        lambda: r.post(
            "/api/batch-digest",
            {
                "records": [
                    {"name": "EGFP_CDS", "topology": "linear", "content": EGFP_CDS},
                    {"name": "mCherry_CDS", "topology": "linear", "content": MCHERRY_CDS},
                    {"name": "pUC19_MCS", "topology": "circular", "content": PUC19_MCS},
                ],
                "enzymes": "EcoRI,BamHI,HindIII",
            },
        ),
    )
    r.check(
        "cdna_map",
        "Map cDNA to genome using EGFP-derived exon model",
        lambda: r.post(
            "/api/cdna-map",
            {
                "cdna_sequence": EGFP_CDS[:210],
                "genome_sequence": EGFP_CDS[:90] + "TTTTTTTTTTTTTTTTTTTT" + EGFP_CDS[90:210],
                "min_exon_bp": 24,
                "max_intron_bp": 200,
            },
        ),
    )
    r.check(
        "contig_assemble",
        "Assemble overlapping reads from EGFP sequence",
        lambda: r.post(
            "/api/contig-assemble",
            {"reads": [EGFP_CDS[:220], EGFP_CDS[180:420], EGFP_CDS[380:620], EGFP_CDS[580:]], "min_overlap": 35},
        ),
    )
    r.check(
        "gibson_assemble",
        "Gibson assembly with EGFP fragments",
        lambda: r.post("/api/gibson-assemble", {"fragments": [EGFP_CDS[:280], EGFP_CDS[240:520], EGFP_CDS[480:]], "min_overlap": 40}),
    )
    r.check(
        "in_fusion",
        "In-Fusion assembly with overlapping EGFP fragments",
        lambda: r.post("/api/in-fusion", {"fragments": [EGFP_CDS[:260], EGFP_CDS[230:490], EGFP_CDS[460:]], "min_overlap": 30, "circular": False}),
    )
    r.check(
        "overlap_extension_pcr",
        "Overlap extension PCR from EGFP split fragments",
        lambda: r.post("/api/overlap-extension-pcr", {"fragment_a": EGFP_CDS[:380], "fragment_b": EGFP_CDS[340:], "min_overlap": 30}),
    )
    r.check(
        "golden_gate",
        "Golden Gate simulation with realistic coding parts",
        lambda: r.post(
            "/api/golden-gate",
            {
                "parts": [
                    {"sequence": EGFP_CDS[:90], "left_overhang": "AATG", "right_overhang": "GGCC"},
                    {"sequence": EGFP_CDS[90:180], "left_overhang": "GGCC", "right_overhang": "TTAA"},
                ],
                "circular": False,
                "enforce_complement": False,
            },
        ),
    )
    r.check(
        "gateway_cloning",
        "Gateway LR-style cloning simulation",
        lambda: r.post(
            "/api/gateway-cloning",
            {
                "entry_clone": "ACAAGTTTGTACAAAAAAGCAGGCT" + EGFP_CDS[:120] + "ACCACTTTGTACAAGAAAGCTGGGT",
                "destination_vector": PUC19_MCS + "TTTGGGCCCAAA",
            },
        ),
    )
    r.check(
        "topo_cloning",
        "TOPO cloning simulation",
        lambda: r.post("/api/topo-cloning", {"vector": PUC19_MCS, "insert": EGFP_CDS[:149] + "A", "mode": "TA"}),
    )
    r.check(
        "ta_gc_cloning",
        "TA/GC cloning simulation",
        lambda: r.post("/api/ta-gc-cloning", {"vector": PUC19_MCS, "insert": "C" + EGFP_CDS[:149], "mode": "GC"}),
    )
    r.check(
        "cloning_compatibility",
        "Compatibility check for restriction cloning setup",
        lambda: r.post(
            "/api/cloning-compatibility",
            {"mode": "restriction", "vector": PUC19_MCS + "TTTT", "insert": "GAATTC" + EGFP_CDS[:120] + "AAGCTT", "enzymes": "EcoRI,HindIII"},
        ),
    )
    r.check(
        "ligation_sim",
        "Predict ligation product distributions",
        lambda: r.post(
            "/api/ligation-sim",
            {
                "vector_sequence": PUC19_MCS + "TTTTGGGGCCCC",
                "insert_sequence": "GGATCC" + EGFP_CDS[:120] + "GAATTC",
                "vector_left_enzyme": "EcoRI",
                "vector_right_enzyme": "BamHI",
                "insert_left_enzyme": "BamHI",
                "insert_right_enzyme": "EcoRI",
                "include_byproducts": True,
                "star_activity_level": 0.2,
            },
        ),
    )

    r.check(
        "project_save",
        "Save a real-world project",
        lambda: r.post("/api/project-save", {**egfp_payload, "project_name": r.created["project"], "history": [EGFP_CDS[:120], EGFP_CDS]}),
    )
    r.check("project_load", "Load saved project", lambda: r.post("/api/project-load", {"project_name": r.created["project"]}))
    r.check("project_list", "List project catalog", lambda: r.post("/api/project-list", {}))
    r.check("project_history_graph", "Build project history graph data", lambda: r.post("/api/project-history-graph", {"project_name": r.created["project"]}))
    r.check("project_history_svg", "Render project history SVG", lambda: r.post("/api/project-history-svg", {"project_name": r.created["project"]}))
    r.check(
        "workspace_create",
        "Create collaboration workspace",
        lambda: r.post(
            "/api/workspace-create",
            {"workspace_name": "rw_workspace", "owner": "owner_user", "members": ["reviewer_user", "editor_user"]},
        ),
    )
    r.check(
        "project_permissions_set",
        "Assign reviewer role for project",
        lambda: r.post("/api/project-permissions", {"project_name": r.created["project"], "roles": {"reviewer_user": "reviewer"}}),
    )
    r.check(
        "project_permissions_get",
        "Read project permission map",
        lambda: r.post("/api/project-permissions", {"project_name": r.created["project"]}),
    )
    r.check(
        "project_audit_log",
        "Fetch project audit log",
        lambda: r.post("/api/project-audit-log", {"project_name": r.created["project"], "limit": 200}),
    )
    r.check(
        "project_diff",
        "Compare project snapshot against edited variant",
        lambda: r.post(
            "/api/project-diff",
            {
                "project_a": {**egfp_payload, "project_name": "egfp_base"},
                "project_b": {**egfp_payload, "project_name": "egfp_mod", "content": f">EGFP\n{EGFP_CDS[:120]}GCC{EGFP_CDS[123:]}"},
            },
        ),
    )
    def _review_flow() -> dict[str, Any]:
        sub = r.post("/api/review-submit", {"project_name": r.created["project"], "submitter": "editor_user", "summary": "ready for release"})
        rid = sub["review"]["review_id"]
        app = r.post(
            "/api/review-approve",
            {"review_id": rid, "project_name": r.created["project"], "reviewer": "reviewer_user", "note": "looks good"},
        )
        return {"review_id": rid, "status": app["review"]["status"]}

    r.check("review_submit_approve", "Submit and approve review workflow", _review_flow)
    r.check("collection_save", "Save collection with project", lambda: r.post("/api/collection-save", {"collection_name": r.created["collection"], "projects": r.created["project"]}))
    r.check("collection_load", "Load collection", lambda: r.post("/api/collection-load", {"collection_name": r.created["collection"]}))
    r.check("collection_list", "List collections", lambda: r.post("/api/collection-list", {}))
    r.check("collection_add_project", "Add project to collection", lambda: r.post("/api/collection-add-project", {"collection_name": r.created["collection"], "project_name": r.created["project"]}))

    def _share_bundle() -> dict[str, Any]:
        d = r.post("/api/share-create", {"projects": [r.created["project"]], "include_content": True})
        sid = d["share_id"]
        r.post("/api/share-load", {"share_id": sid})
        html = r.get("/share/" + sid)
        assert "Shared Bundle" in html
        return {"share_id": sid, "html_bytes": len(html)}

    r.check("share_create_load_get", "Create/load/share bundle over HTTP", _share_bundle)
    r.check("collection_delete", "Delete collection", lambda: r.post("/api/collection-delete", {"collection_name": r.created["collection"]}))
    r.check("project_delete", "Delete project", lambda: r.post("/api/project-delete", {"project_name": r.created["project"]}))
    r.check("root_page", "Ensure UI root page loads", lambda: {"contains_genome_forge": "Genome Forge" in r.get("/")})

    return r.summary(), r.steps


def cleanup_artifacts() -> None:
    for d in ["projects", "collections", "shares", "annotation_db", "enzyme_sets", "collab_data", "reference_db"]:
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p)


def render_markdown_report(summary: dict[str, Any], steps: list[StepResult], output_path: Path) -> None:
    lines: list[str] = []
    lines.append("# Real-World Functional Test Report")
    lines.append("")
    lines.append(f"- Date: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    lines.append(f"- Total Steps: {summary['total_steps']}")
    lines.append(f"- Passed: {summary['passed']}")
    lines.append(f"- Failed: {summary['failed']}")
    lines.append("")
    lines.append("## Data Sources Used")
    lines.append("")
    lines.append("- EGFP CDS (widely used GFP coding sequence, 720 bp including stop)")
    lines.append("- mCherry CDS (widely used red fluorescent protein coding sequence)")
    lines.append("- pUC19 MCS sequence (common cloning vector MCS region)")
    lines.append("")
    lines.append("## Step-by-Step Results")
    lines.append("")
    lines.append("| Step | Objective | Status | Time (ms) | Key Details / Error |")
    lines.append("|---|---|---|---:|---|")
    for s in steps:
        status = "PASS" if s.status == "PASS" else "FAIL"
        if s.status == "PASS":
            detail_txt = ", ".join(f"{k}={v}" for k, v in list(s.details.items())[:4]) or "ok"
        else:
            detail_txt = s.error.replace("|", "/")
        lines.append(f"| `{s.name}` | {s.objective} | **{status}** | {s.duration_ms} | {detail_txt} |")
    lines.append("")
    if summary["failed"]:
        lines.append("## Failures")
        lines.append("")
        for f in summary["failures"]:
            lines.append(f"- `{f['name']}`: {f['error']}")
    else:
        lines.append("## Conclusion")
        lines.append("")
        lines.append("All real-world functional test steps passed.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run comprehensive real-world functional tests")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8122)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--report", default="docs/test_reports/REAL_WORLD_FUNCTIONAL_TEST_REPORT.md")
    ap.add_argument("--json", default="docs/test_reports/REAL_WORLD_FUNCTIONAL_TEST_RESULT.json")
    args = ap.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    server = subprocess.Popen(
        ["python3", "web_ui.py", "--host", args.host, "--port", str(args.port)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_until_ready(base_url, timeout_s=14.0)
        summary, steps = run_real_world_suite(base_url, verbose=args.verbose)
        report_path = ROOT / args.report
        result_path = ROOT / args.json
        render_markdown_report(summary, steps, report_path)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                {
                    "summary": summary,
                    "steps": [
                        {
                            "name": s.name,
                            "objective": s.objective,
                            "status": s.status,
                            "duration_ms": s.duration_ms,
                            "details": s.details,
                            "error": s.error,
                        }
                        for s in steps
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
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
