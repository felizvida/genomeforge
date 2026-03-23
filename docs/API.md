# API Reference

All `/api/*` endpoints are `POST` JSON unless noted otherwise.

This file is also used as a machine-checked inventory surface by `docs/validate_docs.py`. If an endpoint is added or removed in `web_ui.py`, update this file in the same change.

## Record Conversion And Interoperability

- `POST /api/canonicalize-record`
- `POST /api/convert-record`
- `POST /api/import-dna`
- `POST /api/export-dna`
- `POST /api/import-ab1`
- `POST /api/trace-summary`
- `POST /api/trace-align`
- `POST /api/trace-edit-base`
- `POST /api/trace-consensus`
- `POST /api/trace-chromatogram-svg`
- `POST /api/trace-verify`

## Core Sequence And Translation

- `POST /api/info`
- `POST /api/translate`
- `POST /api/translated-features`
- `POST /api/translated-feature-edit`
- `POST /api/protein-edit`
- `POST /api/sequence-edit`
- `POST /api/reverse-translate`
- `POST /api/codon-optimize`
- `POST /api/orfs`
- `POST /api/motif`

## Visualization

- `POST /api/map`
- `POST /api/sequence-tracks`
- `POST /api/sequence-analytics-svg`
- `POST /api/comparison-lens-svg`
- `POST /api/alignment-heatmap-svg`
- `POST /api/project-history-svg`

## Restriction Enzymes And Digest Workflows

- `POST /api/digest`
- `POST /api/digest-advanced`
- `POST /api/star-activity-scan`
- `POST /api/enzyme-scan`
- `POST /api/enzyme-info`
- `POST /api/enzyme-set-save`
- `POST /api/enzyme-set-list`
- `POST /api/enzyme-set-predefined`
- `POST /api/enzyme-set-load`
- `POST /api/enzyme-set-delete`
- `POST /api/batch-digest`

## Primers, PCR, And Mutagenesis

- `POST /api/primers`
- `POST /api/primer-diagnostics`
- `POST /api/primer-specificity`
- `POST /api/primer-rank`
- `POST /api/pcr`
- `POST /api/pcr-gel-lanes`
- `POST /api/anneal-oligos`
- `POST /api/mutagenesis`
- `POST /api/overlap-extension-pcr`

## Alignment, Assembly, And Comparative Analysis

- `POST /api/pairwise-align`
- `POST /api/multi-align`
- `POST /api/msa`
- `POST /api/alignment-consensus`
- `POST /api/phylo-tree`
- `POST /api/contig-assemble`
- `POST /api/cdna-map`
- `POST /api/blast-search`
- `POST /api/search-entities`

## Annotation, Features, References, And RNAi

- `POST /api/annotate-auto`
- `POST /api/annot-db-save`
- `POST /api/annot-db-list`
- `POST /api/annot-db-load`
- `POST /api/annot-db-apply`
- `POST /api/reference-db-save`
- `POST /api/reference-db-list`
- `POST /api/reference-db-load`
- `POST /api/reference-scan`
- `POST /api/features-list`
- `POST /api/features-add`
- `POST /api/features-update`
- `POST /api/features-delete`
- `POST /api/sirna-design`
- `POST /api/sirna-map`

## Cloning And Construct Design

- `POST /api/gibson-assemble`
- `POST /api/golden-gate`
- `POST /api/gateway-cloning`
- `POST /api/topo-cloning`
- `POST /api/ta-gc-cloning`
- `POST /api/cloning-compatibility`
- `POST /api/ligation-sim`
- `POST /api/in-fusion`

## Genome Editing

- `POST /api/grna-design`
- `POST /api/crispr-offtarget`
- `POST /api/hdr-template`

## Gel Simulation

- `POST /api/gel-sim`
- `POST /api/gel-marker-sets`

## Project, Collections, Sharing, And Review

- `POST /api/workspace-create`
- `POST /api/project-permissions`
- `POST /api/project-audit-log`
- `POST /api/project-diff`
- `POST /api/review-submit`
- `POST /api/review-approve`
- `POST /api/project-save`
- `POST /api/project-load`
- `POST /api/project-list`
- `POST /api/project-delete`
- `POST /api/project-history-graph`
- `POST /api/collection-save`
- `POST /api/collection-load`
- `POST /api/collection-list`
- `POST /api/collection-delete`
- `POST /api/collection-add-project`
- `POST /api/share-create`
- `POST /api/share-load`

## Non-API Route

- `GET /share/<share_id>`

## Notes

- The API is intentionally local-first and currently served by Python stdlib HTTP infrastructure.
- Many endpoints return JSON plus embedded SVG payloads for visualization.
- Some biological algorithms are heuristic by design and should be interpreted alongside validation evidence.
