# Feature Coverage (Current Project)

Source list: feature categories tracked from major commercial DNA workbench products.

Legend:
- `Implemented`: available now in CLI or Web UI
- `Partial`: available as simplified approximation
- `Not yet`: not implemented in this project yet

## Molecular Cloning
- Restriction Cloning: `Implemented` (digest simulation + map + compatibility checks + ligation workflows)
- Gateway Cloning: `Implemented` (simplified recombination workflow endpoint)
- Gibson Assembly: `Implemented` (overlap-based assembly workflow)
- NEBuilder HiFi Assembly: `Implemented` (covered by overlap-assembly workflow)
- In-Fusion Cloning: `Implemented` (homology-arm assembly simulation)
- TA & GC Cloning: `Implemented` (TA/GC cloning simulation endpoint)
- TOPO Cloning: `Implemented` (TA/BLUNT cloning simulation endpoint)
- Sticky-end ligation products: `Implemented` (enzyme-end object model + sequence-derived ends + byproduct ranking/probability scoring + star/phosphatase model + junction/scar/frame diagnostics + interactive pathway graph)

## Primers
- Design primers: `Implemented`
- Primer diagnostics: `Implemented` (TmNN + dimer/hairpin heuristics)
- Primer specificity / off-target ranking: `Implemented` (local background scan + pair risk score + candidate ranking)
- Anneal two oligos: `Implemented` (heuristic overlap anneal)

## PCR and Mutagenesis
- Simulate PCR: `Implemented`
- Overlap extension PCR: `Implemented` (overlap-extension PCR simulator)
- Primer-directed mutagenesis: `Implemented` (sequence replacement workflow)

## Enzyme Sets
- Predefined enzyme sets: `Implemented` (built-in predefined sets + custom sets)
- Create custom enzyme sets: `Implemented` (save/list/load/delete + digest-by-set)
- Detailed enzyme information: `Implemented` (metadata endpoint)
- Methylation sensitivity: `Implemented` (methylation-aware digest filtering)
- Star activity analysis: `Implemented` (off-target star-cut scan + optional star-inclusive digest fragments + risk visualization)

## Convert File Formats
- Multiple proprietary formats: `Partial` (Genome Forge DNA container export/import implemented; native proprietary binary `.dna` parsing remains limited)
- FASTA + GenBank import/export: `Implemented`

## Agarose Gel Simulation
- Simulate agarose gel: `Implemented` (approximate migration)
- Simulate restriction digest lanes: `Implemented`
- Simulate PCR amplification lanes: `Implemented` (PCR product lane simulation + marker ladders)
- Large marker collections: `Implemented` (multiple marker-set presets: 1kb+, 100bp, ultra-low, high-range)

## Features / Annotations
- Create/edit features: `Implemented` (feature list/add/update/delete APIs + UI controls)
- Automatic annotation: `Implemented` (motif + ORF heuristics + curated signature DB application)
- Manual novel features: `Implemented` (feature add/update/delete workflows for arbitrary feature keys/locations)
- Choose alternative codons: `Implemented` (codon optimize)
- Sophisticated translated numbering: `Implemented` (translated-feature report with codon/genomic coordinate numbering)
- Ribosomal slippage: `Implemented` (optional +/-1 slippage model in translated-feature report)
- CRISPR helper workflows: `Implemented` (gRNA candidate design + off-target scan + HDR donor template generator)

## Translations
- View/edit translated features: `Implemented` (translated feature report + codon-level translated feature edit API/UI)
- ORFs: `Implemented`
- Whole-sequence translations: `Implemented`
- Reading frame checks: `Implemented` (frame-aware translation lanes + translated-feature codon numbering/slippage checks)
- Make Protein (from DNA): `Implemented`
- Reverse Translate (from Protein): `Implemented`

## Alignment
- Align DNA to reference: `Implemented` (global pairwise)
- Verify cloning/mutagenesis: `Implemented` (compatibility checks + pairwise diagnostics + junction integrity diagnostics)
- cDNA to chromosome: `Implemented` (heuristic exon/intron cDNA-to-genome mapping endpoint)
- Pairwise DNA/protein: `Implemented` (global pairwise for DNA and protein modes)
- Multiple alignment: `Implemented` (progressive MSA + external aligner adapters)
- Choice of algorithms (Clustal/MAFFT/MUSCLE/T-Coffee): `Implemented` (adapters for Clustal/MAFFT/MUSCLE/T-Coffee with fallback)
- Contig assembly: `Implemented` (greedy overlap contig assembler)

## Visualizing
- Multiple sequence views: `Implemented` (sequence tracks + MSA identity heatmap + star-activity risk panel + interactive map/track inspector with zoom/pan + minimap brush navigation)
- Large sequence support: `Implemented` (windowed sequence track + minimap navigation for long sequences)
- Edit DNA/protein sequences: `Implemented` (DNA edit + protein-level codon edit)
- Color coding: `Implemented` (map, sequence track, and UI color themes)

## History Tracking
- Comprehensive undo: `Implemented` (UI undo/redo with persisted local history state)
- Graphical history: `Implemented` (project history graph data + SVG rendering)
- Change coloring by recency: `Implemented` (project history graph node coloring by version recency)
- Audit trail: `Implemented` (project audit-log endpoint with mutation event capture for save/delete + manual event append)

## Data Management
- Import common formats with annotations: `Implemented` (FASTA/GenBank/EMBL parsing with feature import)
- Export standard formats: `Implemented` (FASTA/GenBank)
- Collections and sharing workflows: `Implemented` (local collection save/load/list/delete + add-project workflow)
- Viewer sharing: `Implemented` (local share-bundle create/load + `/share/<id>` HTML viewer pages)
- Batch operations: `Implemented` (batch digest)
- Project persistence: `Implemented` (save/load/list/delete local project JSON)
- Team collaboration core: `Implemented` (workspace creation + per-project role map + review submit/approve workflow + project diff endpoint)

## Search
- Search DNA/protein: `Implemented` (DNA motif search)
- Search enzymes/features/primers: `Implemented` (unified entity search endpoint for motif/features/primer hits)

## General
- Cross platform (Windows/macOS/Linux): `Implemented` (Python runtime-based)

## Summary
This project now covers a broad, practical subset of genome engineering functionality, but does **not** yet provide full parity with all commercial and algorithmic features in the tracked commercial category list.
