# SnapGene-Inspired Toolkit

This repository includes a Python CLI (`snapgene_like.py`) that implements practical DNA sequence design/analysis features inspired by SnapGene.

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
- Sequence export to FASTA/GenBank (`export`)
- Feature listing (`features`)

## Usage

```bash
python3 snapgene_like.py <input_file> info
python3 snapgene_like.py <input_file> digest EcoRI BamHI
python3 snapgene_like.py <input_file> primers --target-start 100 --target-end 900 --na-mM 50 --primer-nM 250
python3 snapgene_like.py <input_file> primer-check --primer ATGCGTACGTTAGC --with-primer CGAACCGTATCGTA
python3 snapgene_like.py <input_file> pcr --forward ATGCGTACGTTAGC --reverse CGAACCGTATCGTA
python3 snapgene_like.py <input_file> codon-optimize --host ecoli --output optimized.fasta
python3 snapgene_like.py <input_file> map --output plasmid_map.svg --enzymes EcoRI BamHI
python3 snapgene_like.py <input_file> export --format genbank --output out.gbk
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

The UI supports:
- Sequence info and translation
- Restriction digest + SVG map rendering
- Annotation-aware sequence track SVG (feature blocks, strand arrows, CDS phase labels, translation frame lane with codon tooltips)
- Interactive map/track navigation (wheel zoom, drag pan, reset controls) with click-to-inspect feature/cut/codon metadata
- Long-sequence track minimap with draggable brush window and quick window-shift controls
- Methylation-aware digest simulation
- Star activity off-target scan with mismatch-tolerant cut discovery
- Enzyme metadata lookup
- Custom enzyme set save/load/list/delete and digest-by-set
- Predefined built-in enzyme sets
- Primer pair design and virtual PCR
- Primer diagnostics (TmNN with salt/primer concentration, dimer/hairpin risk report)
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
- Cloning compatibility checks (restriction/golden-gate/gibson/in-fusion rule checks)
- Sticky-end ligation product simulation with orientation prediction
- Sequence-derived sticky ends from cut sites (optional) with ranked byproduct classes, condition-adjusted probabilities, star-activity risk flags, and phosphatase-treated vector mode
- Junction integrity diagnostics for ligation products (scar sequence, expected site recreation, fusion frame impact)
- Interactive ligation pathway graph (substrate-to-product flow with probability-weighted edges and clickable product diagnostics)
- Interactive star-activity risk visualization (enzyme burden ranking + off-target summary cards)
- Project persistence (save/load/list/delete)
- Project collections (save/load/list/delete + add project)
- Local share bundles (create/load portable JSON snapshots)
- Share-view pages at `/share/<share_id>`
- Feature editor APIs (list/add/update/delete)
- Project history graph endpoint
- Project history graph SVG rendering in UI with recency-based node coloring
- Translated feature reports with codon/genomic coordinate numbering and optional +/-1 slippage simulation

## Notes

- This is not a full reimplementation of proprietary SnapGene software.
- It is a practical open-source subset suitable for common molecular biology workflows.
- Primer Tm in design/QC uses nearest-neighbor approximation plus simple secondary-structure heuristics.
- Feature coverage is broad but still an open-source approximation of SnapGene, not full proprietary parity.
