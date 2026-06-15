# Geneious Prime Feature Priorities

Date: 2026-06-15

This note captures the most desirable Geneious Prime-style workflows to emulate in Genome Forge. It is based on the public Geneious Prime feature page and testimonial language available on 2026-06-15.

Source:

- <https://www.geneious.com/features/prime>

## Most Loved Capabilities

1. Intuitive, visual sequence analysis that makes maps, alignments, traces, and annotations easy to inspect.
2. Sanger sequencing workflows for trace viewing, contig/consensus review, disagreement resolution, SNP/variant calling, and construct confirmation.
3. Annotation and prediction workflows that transfer useful features from public or local reference records onto new constructs.
4. Primer design, primer specificity testing, and primer physical-property screening.
5. Molecular cloning simulation and validation, including restriction, Gibson, Golden Gate, ligation, and lineage-style construct reasoning.
6. Local and external search, especially BLAST-like identity checks against public or private databases.
7. Folder/project organization, metadata, collaboration, and reproducible handoff.
8. Automated workflows that reduce repetitive analysis and make failure points easier to identify.

## Implemented In This Pass

- `/api/annotation-transfer`: similarity-based annotation transfer from annotated reference records or saved reference libraries onto the current record. It reports identity, reference coverage, feature coverage, source record, target coordinates, and optional feature insertion.
- `/api/sanger-consensus`: multi-read Sanger consensus and variant validation. It accepts cached trace IDs, trace records, or plain read sequences; reports consensus calls, unexpected variants, mixed-position disagreements, expected genotype checks, read-level summaries, and a PASS/FAIL verdict.

## Test Strategy

The new regression tests use common molecular-biology data patterns rather than toy strings:

- pUC19 multiple-cloning-site sequence plus EGFP CDS to validate annotation transfer of reporter features into a candidate plasmid context.
- EGFP-derived Sanger read panels to validate expected variant confirmation, mixed evidence reporting, and failure on unexpected variants.

These tests are intentionally deterministic and local-first, so they can run in CI without public database access while still representing realistic bench decisions.
