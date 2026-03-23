# Changelog

All notable changes to Genome Forge are documented in this file.

## [Unreleased]

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
