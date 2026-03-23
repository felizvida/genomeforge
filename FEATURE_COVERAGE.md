# Feature Coverage

This document tracks what Genome Forge can do today and how much confidence to place in each area.

Interpret the columns as follows:

- `Availability`: whether the workflow is present in the product today.
- `Maturity`: how close the implementation is to something we would trust for regular lab use.
- `Validation`: how strongly the workflow is exercised by automated checks.

Legend:

- `Availability`: `Available`, `Out of scope`
- `Maturity`: `Production-ready`, `Validated heuristic`, `Experimental`
- `Validation`: `Suite` (broad smoke or real-world coverage), `Focused` (targeted unit/integration tests), `Basic` (light automated coverage only)

## Molecular Cloning

| Feature | Availability | Maturity | Validation | Notes |
| --- | --- | --- | --- | --- |
| Restriction cloning | Available | Validated heuristic | Suite | Digest simulation, compatibility checks, ligation ranking, and map rendering are all present. |
| Gibson assembly | Available | Validated heuristic | Suite | Overlap-based assembly workflow is implemented and regression-tested. |
| NEBuilder HiFi-style assembly | Available | Experimental | Basic | Covered through the same overlap assembly model rather than a vendor-specific formulation. |
| In-Fusion cloning | Available | Experimental | Focused | Homology-arm assembly workflow is present, but still adapter-style rather than full commercial fidelity. |
| Gateway cloning | Available | Experimental | Focused | Simplified recombination workflow intended for planning, not full proprietary rule parity. |
| TOPO cloning | Available | Experimental | Focused | Simplified TOPO/TA-style planning workflow. |
| TA and GC cloning | Available | Experimental | Focused | Available through dedicated simulation endpoints. |
| Sticky-end ligation product ranking | Available | Validated heuristic | Suite | Includes end matching, byproduct ranking, junction diagnostics, and pathway graphing. |

## Primers, PCR, and Mutagenesis

| Feature | Availability | Maturity | Validation | Notes |
| --- | --- | --- | --- | --- |
| Primer design | Available | Validated heuristic | Suite | Core design workflow is broadly exercised. |
| Primer diagnostics | Available | Validated heuristic | Focused | Includes Tm, dimer, and hairpin heuristics. |
| Primer specificity and off-target ranking | Available | Experimental | Focused | Local background scan and ranking are useful, but not a substitute for a full genomic specificity engine. |
| Virtual PCR | Available | Validated heuristic | Suite | PCR prediction is covered in the broad regression suites. |
| Overlap-extension PCR | Available | Experimental | Focused | Workflow exists and is test-backed, but still heuristic. |
| Primer-directed mutagenesis | Available | Validated heuristic | Suite | Sequence replacement and verification flows are implemented. |
| Oligo annealing | Available | Validated heuristic | Focused | Two-oligo annealing uses overlap heuristics. |

## Enzymes, Digests, and Gels

| Feature | Availability | Maturity | Validation | Notes |
| --- | --- | --- | --- | --- |
| Restriction digest simulation | Available | Validated heuristic | Suite | Core digest workflows are part of the main smoke path. |
| Predefined enzyme sets | Available | Validated heuristic | Focused | Built-in collections plus custom set support. |
| Custom enzyme sets | Available | Validated heuristic | Focused | Save, load, list, and delete are implemented. |
| Enzyme metadata lookup | Available | Validated heuristic | Focused | Detailed enzyme info endpoint is present. |
| Methylation-sensitive digest filtering | Available | Experimental | Focused | Useful planning aid, but still simplified. |
| Star activity analysis | Available | Experimental | Focused | Risk scoring and visualization are available. |
| Agarose gel simulation | Available | Validated heuristic | Suite | Approximate migration model with digest and PCR lanes. |
| Marker-set presets | Available | Validated heuristic | Focused | Includes multiple ladder collections. |

## Annotations, Features, and Translation

| Feature | Availability | Maturity | Validation | Notes |
| --- | --- | --- | --- | --- |
| Feature create, edit, and delete | Available | Production-ready | Suite | CRUD operations are stable and broadly exercised. |
| Automatic annotation | Available | Validated heuristic | Suite | Motif, ORF, and curated-signature approaches are available. |
| Manual novel feature annotation | Available | Production-ready | Suite | Arbitrary feature entry and editing workflows are stable. |
| Reference element libraries and auto-flagging | Available | Validated heuristic | Suite | Save, load, scan, and feature-flag flows are implemented. |
| Whole-sequence translation | Available | Validated heuristic | Suite | Standard translation views are available. |
| ORF detection | Available | Validated heuristic | Suite | Included in both info and annotation workflows. |
| Translated feature view and edit | Available | Experimental | Focused | Codon-level translated editing exists, but is still a higher-risk workflow. |
| Reverse translation | Available | Experimental | Focused | Available for planning, not codon-context-perfect recreation. |
| Reading frame checks | Available | Validated heuristic | Focused | Exposed through translated lanes and translated-feature reporting. |
| Alternative codon choice and codon optimization | Available | Validated heuristic | Suite | Host-aware codon optimization is implemented. |
| Sophisticated translated numbering | Available | Experimental | Focused | Codon and genomic coordinate reporting exists with useful, but simplified, numbering support. |
| Ribosomal slippage modeling | Available | Experimental | Basic | Optional slippage handling exists, but should be treated as exploratory. |

## Alignment, Verification, and Search

| Feature | Availability | Maturity | Validation | Notes |
| --- | --- | --- | --- | --- |
| Pairwise DNA alignment | Available | Validated heuristic | Suite | Core pairwise workflows are broadly exercised. |
| Pairwise protein alignment | Available | Validated heuristic | Focused | Supported in the same analysis layer. |
| Multiple sequence alignment | Available | Validated heuristic | Suite | Progressive MSA plus optional external adapters. |
| Choice of aligners (Clustal, MAFFT, MUSCLE, T-Coffee) | Available | Experimental | Basic | Adapter-backed and dependent on external tools being installed. |
| Contig assembly | Available | Experimental | Focused | Greedy overlap assembly is available for lightweight use. |
| Clone and mutagenesis verification | Available | Validated heuristic | Suite | Pairwise diagnostics and junction integrity checks are implemented. |
| Trace-based plasmid verification and genotyping | Available | Validated heuristic | Suite | Trace comparison, genotype calling, and chromatogram workflows are present. |
| Raw Sanger chromatogram visualization | Available | Validated heuristic | Suite | AB1-aware chromatogram rendering now respects sample positions. |
| cDNA-to-genome mapping | Available | Experimental | Focused | Heuristic exon-intron mapping exists and is useful for teaching or quick inspection. |
| BLAST-like nucleotide database search | Available | Experimental | Suite | Local seed-and-align search helps rank related sequences, but is not a true BLAST replacement. |
| DNA and protein motif/entity search | Available | Validated heuristic | Focused | Unified search covers motifs, features, primers, and related objects. |

## CRISPR and RNAi Design

| Feature | Availability | Maturity | Validation | Notes |
| --- | --- | --- | --- | --- |
| gRNA candidate design | Available | Experimental | Focused | Good for early planning, not a full genomic design stack. |
| CRISPR off-target scan | Available | Experimental | Focused | Local off-target scan exists, but should be interpreted conservatively. |
| HDR donor template design | Available | Experimental | Focused | Template-generation workflow is implemented. |
| siRNA candidate design | Available | Experimental | Suite | GC-aware scoring and repeat penalties are implemented. |
| siRNA target-site mapping | Available | Experimental | Suite | Strand-aware mapping workflows are present. |

## Visualization and Editing

| Feature | Availability | Maturity | Validation | Notes |
| --- | --- | --- | --- | --- |
| Circular map view | Available | Validated heuristic | Suite | Interactive plasmid-style map with zoom and pan. |
| Sequence track view | Available | Validated heuristic | Suite | Windowed track rendering supports long sequences. |
| Track minimap navigation | Available | Validated heuristic | Suite | Supports fast navigation across large records. |
| MSA identity heatmap | Available | Validated heuristic | Focused | Available after multiple alignment. |
| Sequence analytics lens | Available | Experimental | Focused | GC, skew, complexity, and stop-density lens. |
| Comparison lens hotspot view | Available | Experimental | Focused | Variant density and confidence view for side-by-side comparison. |
| DNA sequence editing | Available | Production-ready | Suite | Core edit and history flows are stable. |
| Protein-level codon editing | Available | Experimental | Focused | Useful but more specialized and less mature than direct DNA editing. |
| Color-coded visualization themes | Available | Production-ready | Basic | Stable UI capability, though mostly a presentation concern. |

## History, Collaboration, and Data Management

| Feature | Availability | Maturity | Validation | Notes |
| --- | --- | --- | --- | --- |
| Undo and redo history | Available | Production-ready | Suite | Local history persistence is stable and broadly exercised. |
| Graphical project history | Available | Validated heuristic | Focused | History graph data and SVG rendering are implemented. |
| Audit trail | Available | Validated heuristic | Focused | Save, delete, and manual event capture are supported. |
| Project save, load, list, delete | Available | Production-ready | Suite | Local project persistence is one of the more stable platform features. |
| Collections | Available | Validated heuristic | Focused | Save, load, list, delete, and add-project flows are present. |
| Share bundles and viewer pages | Available | Validated heuristic | Focused | Local sharing workflow is implemented through bundle generation and `/share/<id>` pages. |
| Lightweight review and approval workflow | Available | Experimental | Focused | Useful for small local teams, but not a full collaboration platform. |
| Workspace and role mapping | Available | Experimental | Focused | Present for lightweight project coordination. |
| Batch digest operations | Available | Validated heuristic | Focused | Bulk digest workflow is available. |
| Import FASTA, GenBank, and EMBL with annotations | Available | Validated heuristic | Suite | Core annotated import flows are well covered. |
| Export FASTA and GenBank | Available | Production-ready | Suite | Standard export flows are stable. |
| Proprietary `.dna` import | Available | Experimental | Basic | Depends on optional Biopython-backed parsing; fidelity varies by source file. |

## Platform and Scope

| Feature | Availability | Maturity | Validation | Notes |
| --- | --- | --- | --- | --- |
| Local-first web UI | Available | Validated heuristic | Suite | Stable for normal usage, but still built on a custom lightweight HTTP entrypoint. |
| Python CLI | Available | Production-ready | Focused | Stable command-line entrypoint for core record operations. |
| Cross-platform runtime (Windows, macOS, Linux) | Available | Production-ready | Basic | Python-based runtime model supports all major desktop platforms. |
| Full vendor-specific binary fidelity for proprietary formats | Out of scope | N/A | N/A | Genome Forge intentionally avoids claiming full parity with commercial vendor binary internals. |

## Summary

Genome Forge now covers the planned workflow surface, but it does not claim that every workflow is equally mature.

- Core record handling, feature editing, local persistence, sequence editing, import/export, and the main digest/map/PCR/verification paths are the strongest areas.
- Many design-assist and analysis-heavy workflows are best described as validated heuristics rather than drop-in replacements for proprietary commercial engines.
- The right way to read the project today is: broad capability, strong momentum, improving architecture, and explicit maturity labeling instead of blanket “implemented” claims.
