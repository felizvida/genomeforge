# User Guide

## Product Model

Genome Forge is a local-first DNA workbench built around:

- a Python sequence engine
- a browser-based web UI
- reproducible tests and training materials

Most users will work through the web UI. The CLI is useful for scripted tasks, export operations, and simple batch usage.

## Starting The Web UI

```bash
python3 web_ui.py --port 8080
```

Open:

```text
http://127.0.0.1:8080
```

## Loading Sequence Data

Genome Forge accepts:

- FASTA
- GenBank
- EMBL
- raw nucleotide sequence
- Genome Forge DNA container payloads
- AB1 trace payloads

Typical sequence entry paths:

- paste content directly into the record input area
- load a saved project or collection
- import a DNA container
- import an AB1 payload for trace workflows

## Core Workflow Families

## 1. Inspect And Visualize

Use this when you want to understand what a sequence is before editing it.

Main tools:

- map rendering
- sequence track rendering
- translation and ORF inspection
- analytics lens and comparison lens
- feature list and entity search

Typical outcome:

- a visual map
- annotation context
- reading frame interpretation
- hotspot or anomaly review

## 2. Design Primers And PCR

Use this when preparing validation, amplification, or screening workflows.

Main tools:

- primer design
- primer diagnostics
- primer specificity and ranking
- virtual PCR
- PCR gel lane simulation

Typical outcome:

- ranked primer pairs
- expected amplicon size
- thermodynamic and off-target risk review

## 3. Plan Cloning And Assembly

Use this when building or validating a plasmid design strategy.

Main tools:

- restriction digest
- methylation-aware digest
- enzyme metadata and enzyme sets
- cloning compatibility checks
- Gibson, Golden Gate, Gateway, TOPO, TA/GC, In-Fusion, and overlap-extension workflows
- ligation simulation and junction diagnostics

Typical outcome:

- enzyme selection
- predicted assembly product
- byproduct risk review
- junction integrity interpretation

## 4. Validate With Sequence Evidence

Use this when confirming that a construct or sample matches expectation.

Main tools:

- pairwise alignment
- multi-sequence alignment
- AB1 trace import, summary, consensus, and chromatogram review
- trace-based verification and genotype calling
- BLAST-like search

Typical outcome:

- identity and mismatch summary
- trace-supported base calls
- reference match or contamination suspicion

## 5. Annotate, Search, And Reuse

Use this when working with known elements, signatures, and recurring design patterns.

Main tools:

- automatic annotation
- annotation database save/load/apply
- reference library save/load/scan
- siRNA design and target mapping
- motif search and unified entity search

Typical outcome:

- reusable reference libraries
- quickly flagged sequence elements
- design-ready target candidates

## 6. Persist, Share, And Review

Use this when you need repeatability and lightweight collaboration.

Main tools:

- project save/load/list/delete
- project history graph and SVG
- collections
- share bundles and `/share/<id>` viewer pages
- workspace creation
- permission map
- audit log
- diff and review submit/approve

Typical outcome:

- reproducible saved states
- reviewable project changes
- portable share artifacts

## CLI Usage

The CLI remains useful for compact local operations:

```bash
python3 genomeforge_toolkit.py input.fasta info
python3 genomeforge_toolkit.py input.fasta digest EcoRI BamHI
python3 genomeforge_toolkit.py input.fasta map --output plasmid_map.svg --enzymes EcoRI BamHI
```

If the project is installed in editable mode:

```bash
genomeforge input.fasta info
```

## Learn The Product

For structured training:

- [Tutorial HTML](tutorial/user_training_tutorial.html)
- [Tutorial PDF](tutorial/user_training_tutorial.pdf)
- [Training Case Playbook](tutorial/datasets/case_playbook.md)
- [Tutorial Dataset Guide](tutorial/datasets/README.md)
