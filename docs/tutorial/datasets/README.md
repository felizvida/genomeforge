# Genome Forge Tutorial Datasets

This folder contains the reproducible sample data used by the self-study tutorial.

## Files

- `training_real_world_sequences.fasta`: public-source base records bundled directly in FASTA.
- `training_real_world_dataset.json`: metadata, sources, case-to-record mapping, and definitions for derived training records.
- `case_playbook.md`: compact tutorial checklist.
- `case_bundles/`: prebuilt ready-to-load bundles for all 39 cases.
- `extract_case_bundle.py`: helper that writes a case-specific FASTA bundle plus a manifest JSON.

## Quick Use

```bash
python3 docs/tutorial/datasets/extract_case_bundle.py --list-cases
python3 docs/tutorial/datasets/extract_case_bundle.py --case A --out ./tmp/genomeforge_case_a
python3 docs/tutorial/datasets/extract_case_bundle.py --case K --out ./tmp/genomeforge_case_k
```

If you want a zero-friction starting point, load the already-generated bundle at `docs/tutorial/datasets/case_bundles/case_a/records.fasta` (or the matching folder for any other case).

## Why derived records exist

Some tutorial cases use clearly labeled training derivatives of public-source records. Those are included so you can practice pairwise comparison, variant interpretation, ambiguity-aware search, and phylogeny-style reasoning on examples with known biological intent.
