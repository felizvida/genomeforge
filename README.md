# Genome Forge Toolkit

This repository includes a Python CLI (`genomeforge_toolkit.py`) for practical DNA sequence design and analysis workflows.

## Implemented functions

- FASTA and GenBank import
- Basic GenBank feature-table parsing
- Sequence summary (`info`)
- Reverse complement (`revcomp`)
- Translation (`translate`)
- ORF finding (`orfs`)
- Restriction digest simulation (`digest`)
- Primer pair design (`primers`)
- Primer QC (`primer-check`)
- Virtual PCR (`pcr`)
- Codon optimization (`codon-optimize`)
- Sequence map rendering to SVG (`map`)
- Sequence export to FASTA/GenBank/EMBL/JSON (`export`)
- Feature listing (`features`)

## Usage

```bash
python3 genomeforge_toolkit.py <input_file> info
python3 genomeforge_toolkit.py <input_file> digest EcoRI BamHI
python3 genomeforge_toolkit.py <input_file> primers --target-start 100 --target-end 900 --na-mM 50 --primer-nM 250
python3 genomeforge_toolkit.py <input_file> primer-check --primer ATGCGTACGTTAGC --with-primer CGAACCGTATCGTA
python3 genomeforge_toolkit.py <input_file> pcr --forward ATGCGTACGTTAGC --reverse CGAACCGTATCGTA
python3 genomeforge_toolkit.py <input_file> codon-optimize --host ecoli --output optimized.fasta
python3 genomeforge_toolkit.py <input_file> map --output plasmid_map.svg --enzymes EcoRI BamHI
python3 genomeforge_toolkit.py <input_file> export --format genbank --output out.gbk
python3 genomeforge_toolkit.py <input_file> export --format embl --output out.embl
python3 genomeforge_toolkit.py <input_file> export --format json --output out.json
```

## Web UI

Run the local web interface:

```bash
python3 web_ui.py --port 8080
```

Then open:

```text
http://127.0.0.1:8080
```

Training materials:
- HTML tutorial: `docs/tutorial/user_training_tutorial.html`
- PDF tutorial: `docs/tutorial/user_training_tutorial.pdf`
- Feature listing: `FEATURE_COVERAGE.md`

The UI supports:
- Sequence info and translation
- Restriction digest + SVG map rendering
- Annotation-aware sequence track SVG (feature blocks, strand arrows, CDS phase labels, translation frame lane with codon tooltips)
- Interactive map/track navigation (wheel zoom, drag pan, reset controls) with click-to-inspect feature/cut/codon metadata
- Long-sequence track minimap with draggable brush window and quick window-shift controls
- Sequence analytics lens visualization (GC%, GC-skew, local complexity, stop-codon density)
- Comparison lens visualization (alignment divergence/confidence tracks with hotspot highlighting)
- Methylation-aware digest simulation
- Star activity off-target scan with mismatch-tolerant cut discovery
- Enzyme metadata lookup
- Custom enzyme set save/load/list/delete and digest-by-set
- Predefined built-in enzyme sets
- Primer pair design and virtual PCR
- Primer diagnostics (TmNN with salt/primer concentration, dimer/hairpin risk report)
- Primer specificity/off-target risk scanning and primer-pair ranking (`/api/primer-specificity`, `/api/primer-rank`)
- PCR gel-lane simulation from primer pairs
- Codon optimization
- ORF browser
- Motif search
- Unified entity search across motifs, features, and primer matches
- Built-in enzyme catalog scan
- In-place sequence editing (insert/delete/replace) with preview/apply
- Protein-level sequence editing via codon substitution
- EMBL format import support (with feature parsing)
- Undo/redo history for sequence edits (persisted in browser storage)
- Pairwise alignment (global DNA + protein modes)
- Multi-sequence reference alignment (reference-vs-each)
- Progressive MSA (with optional MAFFT/MUSCLE/ClustalW adapters if installed)
- Alignment consensus + per-column conservation + identity matrix
- Alignment identity heatmap SVG
- Greedy contig assembly (overlap-based)
- UPGMA phylogeny tree output (Newick + merge steps)
- Reverse translation (protein -> DNA)
- Translated feature codon-level editing for CDS annotations
- Automatic motif-based annotation
- Curated annotation database (save/list/load/apply signatures)
- Oligo annealing simulation
- Primer-directed mutagenesis-style replacement
- Agarose gel band migration approximation with selectable marker ladder presets
- cDNA-to-genome exon/intron mapping (heuristic spliced alignment)
- Batch digest across multiple records
- Gibson-style overlap assembly
- Golden Gate-style overhang assembly
- Gateway-style recombination cloning (simplified)
- TOPO-style cloning (TA/BLUNT simplified)
- TA/GC cloning simulation
- In-Fusion-style homology assembly simulation
- Overlap-extension PCR simulation
- CRISPR helper workflows: gRNA candidate design, off-target scan, HDR donor template design (`/api/grna-design`, `/api/crispr-offtarget`, `/api/hdr-template`)
- Cloning compatibility checks (restriction/golden-gate/gibson/in-fusion rule checks)
- Sticky-end ligation product simulation with orientation prediction
- Sequence-derived sticky ends from cut sites (optional) with ranked byproduct classes, condition-adjusted probabilities, star-activity risk flags, and phosphatase-treated vector mode
- Junction integrity diagnostics for ligation products (scar sequence, expected site recreation, fusion frame impact)
- Interactive ligation pathway graph (substrate-to-product flow with probability-weighted edges and clickable product diagnostics)
- Interactive star-activity risk visualization (enzyme burden ranking + off-target summary cards)
- Canonical schema normalization and converter endpoints (`/api/canonicalize-record`, `/api/convert-record`)
- Genome Forge DNA container export/import (`/api/export-dna`, `/api/import-dna`)
- Visualization APIs for modern analytics overlays (`/api/sequence-analytics-svg`, `/api/comparison-lens-svg`)
- AB1 trace workflow foundation: import/summarize/align/edit/consensus (`/api/import-ab1`, `/api/trace-summary`, `/api/trace-align`, `/api/trace-edit-base`, `/api/trace-consensus`)
- Project persistence (save/load/list/delete)
- Project collections (save/load/list/delete + add project)
- Local share bundles (create/load portable JSON snapshots)
- Share-view pages at `/share/<share_id>`
- Collaboration core: workspace create, project permissions, project audit logs, structured project diff, and review submit/approve workflows
- Feature editor APIs (list/add/update/delete)
- Project history graph endpoint
- Project history graph SVG rendering in UI with recency-based node coloring
- Translated feature reports with codon/genomic coordinate numbering and optional +/-1 slippage simulation

## Notes

- This is an open-source implementation focused on practical molecular biology workflows.
- Primer Tm in design/QC uses nearest-neighbor approximation plus simple secondary-structure heuristics.
- Native proprietary `.dna` import is supported via optional Biopython parser when available (`python3 -m pip install biopython`).
- Some advanced commercial algorithms and proprietary binary internals remain out of scope.
