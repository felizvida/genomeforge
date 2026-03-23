# Changelog

All notable changes to Genome Forge are documented in this file.

## [Unreleased]

### Added

- Added a structured documentation set:
  - `docs/README.md`
  - `docs/INSTALL.md`
  - `docs/USER_GUIDE.md`
  - `docs/DEVELOPER_GUIDE.md`
  - `docs/ARCHITECTURE.md`
  - `docs/API.md`
- Added `pyproject.toml` for package metadata, optional dependency groups, and console entry points.
- Added a `Makefile` for common local development tasks.
- Added `docs/validate_docs.py` to catch documentation drift.
- Added `docs/build_tutorial_pdf.py` for repeatable tutorial PDF generation.
- Added a focused unit-test baseline in `tests/`.

### Changed

- Repositioned the repo around a product-first documentation structure rather than a flat feature dump.
- Updated CI design to support packaging-aware checks, documentation validation, and unit-test expansion.

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
