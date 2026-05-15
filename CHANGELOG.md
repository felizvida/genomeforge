# Changelog

All notable changes to Genome Forge are documented in this file.

## [Unreleased]

## [0.1.10] - 2026-05-15

### Added

- Added in-app Learning Mode for guided flagship workflows.
- Added evidence-to-decision cards that connect workflow outputs to biological inference, confidence limits, and next bench actions.
- Expanded the tutorial generator with exact UI walkthroughs, just-in-time glossary cards, evidence/inference checkpoints, bench decision cards, common wrong interpretations, and lab-chief teaching prompts for all 45 cases.
- Added browser regression coverage for Learning Mode and decision-card updates.

### Changed

- Regenerated the tutorial HTML, PDF, dataset metadata, and case playbook for the new teaching model.
- Updated README, handoff, npm package metadata, Python package metadata, and release notes for the new release.
- Reworked SVG minimap and pan/zoom interactions to use scoped pointer-event listeners instead of brittle handler-property assignment.

### Fixed

- Removed local browser favicon 404 noise with an embedded SVG favicon.
- Preserved feature/cut/codon click inspection while keeping map pan/zoom behavior available.
- Extended documentation validation to catch Python package version drift.

### Validation

- `python3 docs/validate_docs.py`
- `python3 -m py_compile backend/project_api.py collab/store.py docs/tutorial/generate_tutorial.py docs/validate_docs.py docs/tutorial/datasets/extract_case_bundle.py docs/build_tutorial_pdf.py`
- `node --check webui/js/ui-core.js && node --check webui/js/workflows-core.js && node --check webui/js/workflows-analysis.js && node --check webui/js/workflows-search.js && node --check webui/js/workflows-projects.js && node --check webui/js/app.js`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 smoke_test.py`
- `python3 real_world_functional_test.py`
- `npm run test:e2e`

## [0.1.9] - 2026-04-29

### Added

- Added ApE-inspired DNA workflows to the training tutorial, including diagnostic cutter comparison, custom ladder planning, text-map inspection, silent restriction-site engineering, linked trace navigation, and selected-sequence external BLAST launch.
- Added concept illustrations for diagnostic digests, silent restriction-site engineering, and trace-to-reference evidence review.
- Added ready-to-load tutorial case bundles for the six new lessons.

### Changed

- Retitled the course to **Teach Yourself DNA Bioinformatics with Genome Forge** for a more precise scope.
- Rebuilt the tutorial as a US Letter, duplex-oriented print edition with a designed front cover, inside front cover, mirrored gutters, and an even-page back cover.
- Expanded the generated tutorial dataset, playbook, HTML, and PDF to 45 lessons.

### Validation

- Regenerated the tutorial HTML/PDF and dataset artifacts from source.
- Re-ran documentation validation, Python compile checks, PDF geometry checks, and whitespace checks.

## [0.1.8] - 2026-04-27

### Added

- Added regression coverage for collaboration trust boundaries, including owner-only ACL updates, read-only audit retrieval, and escaped share-page metadata.
- Added a refreshed textbook-style tutorial edition with a stronger learning path, polished case hierarchy, and regenerated HTML/PDF artifacts.

### Changed

- Hardened project permission writes so collaborators are merged safely and only a current owner can modify established ACLs.
- Tightened project review approval and audit behavior so review state now depends on verified project roles and audit events are generated internally.
- Reworked tutorial typography and page rhythm for a cleaner publication-style reading experience.

### Fixed

- Fixed a stored HTML-injection path in public share pages by escaping project metadata before rendering.
- Fixed minimap dragging so it no longer overwrites global mouse handlers during repeated track rerenders.

## [0.1.7] - 2026-04-02

### Added

- Added publication-style tutorial front matter including a half-title page, full title page, imprint page, and deeper case-level table of contents.
- Added print-only cluster chapter openers to make the PDF tutorial read more like a formal course reader.
- Added PDF metadata/tagging support in the tutorial build so the exported volume now carries author/subject metadata and reports as a tagged PDF.

### Changed

- Refined the tutorial typesetting for publication-oriented print output with mirrored folios, figure numbering, cleaner chapter rhythm, and better pagination for long tables.
- Tightened front-matter and chapter-opener copy so the tutorial reads more cleanly in the final page design.
- Regenerated the tutorial HTML/PDF after the final layout and editorial pass.

## [0.1.6] - 2026-04-02

### Added

- Added two new ambiguity-aware tutorial lessons:
  - `Case AL`: degenerate primer strategy across a variant family
  - `Case AM`: ambiguity-aware identity search and motif rescue
- Added a new ambiguity-bearing training record to teach IUPAC-aware assay and search behavior explicitly.
- Added flagship UI screenshots for the new ambiguity-aware lessons and refreshed several existing tutorial screenshots for visual consistency.

### Changed

- Reframed the tutorial as a more textbook-like self-study edition with stronger front matter, calmer print styling, and study-note callouts.
- Expanded the training package from 37 to 39 lessons and regenerated the HTML, PDF, dataset metadata, playbook, and per-case bundles to match.
- Updated repo-facing documentation and validation rules to track the new lesson count and tutorial structure.

## [0.1.5] - 2026-04-02

### Added

- Added ambiguity-aware DNA matching semantics across motif search, PCR product detection, BLAST-like local alignment, and primer-specificity workflows.
- Added regression coverage for IUPAC-aware motif matching, PCR amplification, complementarity scoring, BLAST-like search, and primer-specificity reporting.

### Fixed

- Fixed a release-blocking regression in `/api/search-entities` so free-text queries like `gene` no longer get routed through the DNA motif matcher.
- Preserved the prior smoke, real-world, and browser regression baselines after broadening IUPAC handling.

## [0.1.4] - 2026-03-23

### Added

- Added a source-driven tutorial generator at `docs/tutorial/generate_tutorial.py`.
- Added reusable tutorial screenshot capture at `docs/tutorial/capture_tutorial_screenshots.js`.
- Added a dataset guide for the training bundle at `docs/tutorial/datasets/README.md`.
- Added prebuilt per-case bundles for all 37 tutorial cases under `docs/tutorial/datasets/case_bundles/`.
- Added real UI screenshots for flagship workflows directly into the tutorial and README.

### Changed

- Completely rebuilt the tutorial around richer biological meaning, real-world record framing, and clearer sample-data onboarding.
- Refreshed the tutorial HTML/PDF to use included public-source records plus labeled training derivatives.
- Tightened documentation validation so tutorial dataset outputs and screenshot assets are checked explicitly.

## [0.1.3] - 2026-03-16

### Fixed

- Fixed the reference auto-flag workflow so newly detected elements remain visible to the active UI session.
- Fixed BLAST-like local search coverage reporting for partial matches.
- Fixed chromatogram rendering to use raw AB1 sample positions when available.
- Strengthened regression coverage around search, trace rendering, and reference scanning.

## [0.1.2] - 2026-03-04

### Added

- Added BLAST-like local nucleotide search.
- Added Sanger chromatogram rendering.
- Added trace-based verification and genotyping.
- Added reference element library save/load/scan workflows.
- Added siRNA design and mapping workflows.
- Expanded the tutorial to 37 cases with step-by-step guides, sample results, expected results, interpretation notes, and biological explanation sections.

## [0.1.1] - 2026-03-04

### Changed

- Completed the Genome Forge rebrand cleanup across code and docs.
- Expanded and reorganized the training tutorial into 20 biologically clustered cases as part of the earlier tutorial expansion path.
- Refreshed handoff and feature-coverage documentation under Genome Forge naming.

## [0.1.0] - 2026-03-04

### Added

- Released the Genome Forge web workbench with broad cloning and sequence-analysis workflow coverage.
- Added interactive visualization improvements including map and sequence-track exploration.
- Added canonical schema conversion and record round-tripping.
- Added trace workflow foundations, primer specificity workflows, CRISPR helpers, and collaboration core features.
