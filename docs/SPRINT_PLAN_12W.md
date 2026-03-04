# Genome Forge 12-Sprint Implementation Plan

This plan turns the roadmap into concrete repository work.  
Cadence assumes 1-week sprints, one full-time engineer.

## Delivery Goals

1. Native interoperability (`.dna`, `.ab1`) with robust roundtrip behavior.
2. Practical assay-quality design workflows (primer specificity + CRISPR).
3. Team-ready governance and performance for larger records.

## Repo Conventions For New Work

1. Keep format-specific logic under new `compat/`.
2. Keep heavy compute and adapters under new `bio/`.
3. Keep API handlers in `web_ui.py` thin; move logic into imported modules.
4. Add deterministic fixtures and regression tests for every new endpoint.

## Sprint 1: Interop Foundation

1. Create module skeletons:
   - `compat/__init__.py`
   - `compat/dna_format.py`
   - `compat/ab1_format.py`
   - `bio/__init__.py`
2. Add endpoint stubs in `web_ui.py`:
   - `/api/import-dna`
   - `/api/export-dna`
   - `/api/import-ab1`
3. Add fixtures directory:
   - `tests/fixtures/interop/`
4. Add test harness:
   - `tests/test_interop_api.py`

Acceptance:
1. Endpoints exist and validate payloads.
2. Tests run and fail only on unimplemented parsing internals.

## Sprint 2: `.dna` Import (Read Path)

1. Implement `.dna` reader in `compat/dna_format.py`.
2. Map parsed record into existing internal payload shape.
3. Add conversion helpers in `canonical_schema.py` for imported metadata.
4. Add tests:
   - `tests/test_dna_import.py`

Acceptance:
1. Imported `.dna` yields valid `name/topology/sequence/features`.
2. Handles malformed files with clear errors.

## Sprint 3: `.dna` Export (Roundtrip Path)

1. Implement `.dna` writer in `compat/dna_format.py`.
2. Wire `/api/export-dna` in `web_ui.py`.
3. Add roundtrip tests:
   - `tests/test_dna_roundtrip.py`

Acceptance:
1. `import -> export -> import` preserves sequence and core annotations.
2. Non-lossy for supported fields.

## Sprint 4: AB1 Chromatogram Import

1. Implement AB1 parser in `compat/ab1_format.py`:
   - base calls
   - quality scores
   - peak traces (channels)
2. Add endpoints:
   - `/api/trace-summary`
   - `/api/trace-align`
3. Add tests:
   - `tests/test_ab1_import.py`

Acceptance:
1. AB1 upload returns base/quality/trace arrays with stable schema.
2. Trace alignment API returns coordinate mapping and mismatch list.

## Sprint 5: Trace UI + Manual Base Editing

1. Extend UI:
   - `webui/index.html` add Trace tab
2. Add API:
   - `/api/trace-edit-base`
   - `/api/trace-consensus`
3. Add tests:
   - `tests/test_trace_editing.py`

Acceptance:
1. User can inspect peaks, edit base call, recompute consensus.
2. Edit history reflected in project save/load.

## Sprint 6: Primer Specificity Engine (Local)

1. Implement local specificity backend:
   - `bio/primer_specificity.py`
2. Add optional external aligner adapter:
   - `bio/alignment_adapters.py`
3. Add API:
   - `/api/primer-specificity`
   - `/api/primer-rank`
4. Add tests:
   - `tests/test_primer_specificity.py`

Acceptance:
1. Returns ranked off-target report and summary risk score.
2. Works with fallback mode if no external binaries installed.

## Sprint 7: CRISPR Candidate Design

1. Add module:
   - `bio/crispr_design.py`
2. Add API:
   - `/api/grna-design`
   - `/api/crispr-offtarget`
3. UI section in `webui/index.html` (CRISPR controls + result table).
4. Add tests:
   - `tests/test_crispr_design.py`

Acceptance:
1. Candidate generation by PAM pattern and spacer constraints.
2. Off-target report includes genomic position/proxy score breakdown.

## Sprint 8: HDR/Donor Design Workflow

1. Add module:
   - `bio/hdr_template.py`
2. Add API:
   - `/api/hdr-template`
3. UI donor builder in `webui/index.html`.
4. Add tests:
   - `tests/test_hdr_template.py`

Acceptance:
1. Returns donor sequence with configurable arm lengths.
2. Suggests silent PAM-disrupt edits when possible.

## Sprint 9: Collaboration Data Model

1. Introduce lightweight persistence package:
   - `collab/__init__.py`
   - `collab/store.py`
   - `collab/audit.py`
2. Add APIs:
   - `/api/workspace-create`
   - `/api/project-permissions`
   - `/api/project-audit-log`
3. Add tests:
   - `tests/test_collab_permissions.py`

Acceptance:
1. Role-based access checks enforced in APIs.
2. All mutating actions emit audit records.

## Sprint 10: Review/Approval + Compare

1. Add modules:
   - `collab/review.py`
   - `bio/project_diff.py`
2. Add APIs:
   - `/api/project-diff`
   - `/api/review-submit`
   - `/api/review-approve`
3. UI review panel in `webui/index.html`.
4. Add tests:
   - `tests/test_review_flow.py`

Acceptance:
1. Structured record diff available for sequence + features.
2. Review transitions enforce role and state checks.

## Sprint 11: Integration Connectors + Scale Pass

1. Add connectors:
   - `integrations/ncbi.py`
   - `integrations/addgene.py`
2. Add APIs:
   - `/api/import-ncbi`
   - `/api/import-addgene`
3. Long-sequence performance module:
   - `bio/sequence_index.py`
4. Add tests:
   - `tests/test_integrations.py`
   - `tests/test_large_sequence_performance.py`

Acceptance:
1. External import returns canonical payload shape.
2. Track/map interactions remain responsive on long sequences.

## Sprint 12: Hardening + Release

1. Reliability and compatibility audit across all new features.
2. Expand real-world suite:
   - extend `real_world_functional_test.py`
3. Add release docs:
   - `docs/RELEASE_CHECKLIST.md`
   - `docs/MIGRATION_NOTES.md`
4. Final QA report:
   - `docs/test_reports/PHASE2_RELEASE_TEST_REPORT.md`

Acceptance:
1. Full suite green in local CI-style run.
2. Release notes, migration notes, and known limitations documented.

## Cross-Sprint Backlog (Always-On)

1. Refactor `web_ui.py` monolith by extracting feature modules incrementally.
2. Add input schema validation helpers in one place (`validation.py`).
3. Keep API response schemas stable and versioned.
4. Maintain fixture-based regression packs for every format/parser change.

## Suggested Weekly Demo Format

1. Demo of new endpoint(s) and UI flow.
2. Live run of added tests.
3. Risk log update (technical debt, data-quality issues, perf concerns).
4. Updated burndown for next sprint.
