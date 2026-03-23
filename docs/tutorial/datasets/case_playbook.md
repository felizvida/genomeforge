# Genome Forge Training Case Playbook

This playbook is the compact companion to the full tutorial. It mirrors the current 37 tutorial cases and gives a quick reminder of the workflow focus, likely input data, and expected outcome.

## Cluster A: Molecule Architecture And Restriction Logic

## Case A: Restriction Map for Cloning Entry Design

- Focus: render a plasmid map and choose a clean cloning entry strategy
- Data: circular vector record with annotated functional regions
- Expected: map plus digest output showing useful unique or directional cut logic

## Case B: Methylation-Aware Digest Interpretation

- Focus: compare standard digest behavior to methylation-aware predictions
- Data: sequence plus methylation-sensitive enzyme panel
- Expected: blocked-cut explanation and changed fragment expectations

## Case C: Star Activity Risk Review

- Focus: inspect mismatch-tolerant off-target cutting behavior
- Data: enzyme panel and a susceptible sequence context
- Expected: star-risk summary and off-target burden interpretation

## Case U: k-mer Profile for Contamination Suspicion

- Focus: use motif and entity search patterns to suspect mixed-origin sequence
- Data: partially trusted sequence with unusual local composition
- Expected: anomalous motif or feature context that supports contamination triage

## Cluster B: Sequence Meaning And Functional Annotation

## Case D: Sequence Track and Translation Context

- Focus: inspect feature placement, strands, and translation lanes together
- Data: annotated coding sequence
- Expected: sequence track with readable feature and translation context

## Case M: ORF Scan and Coding Potential Triage

- Focus: determine whether a sequence plausibly contains protein-coding content
- Data: raw or weakly annotated DNA sequence
- Expected: ORF inventory and coding-potential interpretation

## Case P: Variant Annotation from Reference-Aligned Edits

- Focus: connect sequence edits to feature context and likely effect
- Data: edited record plus reference sequence
- Expected: variant-aware interpretation of where the edit lands and why it matters

## Case W: Protein Property Inference from Translation

- Focus: translate DNA and reason about resulting protein-level properties
- Data: coding sequence or predicted ORF
- Expected: translated protein plus qualitative interpretation of sequence-driven behavior

## Cluster C: Assay And Primer System Design

## Case E: Primer Design and Thermodynamic Screening

- Focus: design primers around a target window and screen their quality
- Data: target coding sequence and desired amplification region
- Expected: primer pair with Tm, GC, and structure metrics in range

## Case F: Specificity Ranking with Virtual PCR/Gel

- Focus: choose the safer primer pair using specificity and PCR simulation
- Data: primer candidates plus background sequences
- Expected: ranked primer pairs and expected dominant product lane

## Case Q: Multiplex PCR Panel Balancing

- Focus: compare primer systems for compatibility in a panel-like setting
- Data: several primer pairs against shared backgrounds
- Expected: pair ranking and practical tradeoff notes for multiplex use

## Case AA: Positive and Negative Control Design

- Focus: design controls that confirm both assay presence and assay absence
- Data: target and off-target sequence contexts
- Expected: control plan with expected pass/fail readouts

## Cluster D: Assembly And Construct Validation

## Case G: Cloning Compatibility and Ligation Product Ranking

- Focus: check whether a cloning setup is internally coherent
- Data: vector, insert, enzymes, or overlap arms
- Expected: compatibility verdict and ranked ligation or assembly products

## Case S: Circular Construct Integrity and Junction Validation

- Focus: verify that a proposed circular product preserves intended structure
- Data: assembled construct and junction coordinates
- Expected: junction diagnostics including scar and frame interpretation

## Case Z: Multi-Trace Consensus for Final Construct Call

- Focus: combine multiple trace perspectives into one construct verdict
- Data: several sequencing traces against one expected construct
- Expected: consensus-backed final call on construct identity

## Cluster E: Comparative And Population-Level Reasoning

## Case H: MSA, Identity Heatmap, and Phylogeny

- Focus: compare related sequences at multiple scales
- Data: three or more homologous DNA sequences
- Expected: alignment, heatmap, and tree that explain relatedness

## Case N: GC Landscape and Repeat Fragility

- Focus: inspect GC and repeat-rich regions as assay or synthesis risk zones
- Data: long coding or vector sequence
- Expected: analytics-lens regions worth avoiding for assay anchors

## Case O: Homopolymer and Low-Complexity Risk Detection

- Focus: find regions that often produce low-confidence sequencing or synthesis behavior
- Data: sequence with repetitive or simple composition segments
- Expected: low-complexity interpretation and experimental caution notes

## Case X: Motif Enrichment and Significance Framing

- Focus: reason about motif frequency in context rather than by raw count alone
- Data: one or more sequences plus motif of interest
- Expected: motif context interpretation with caution against overclaiming

## Cluster F: Editing And Design For Intervention

## Case K: CRISPR Candidate and HDR Donor Design

- Focus: choose a guide and design a donor template for a precise edit
- Data: target locus and intended edit coordinates
- Expected: gRNA candidates, off-target report, and HDR donor sequence

## Case R: Promoter/RBS Context for Expression Tuning

- Focus: interpret non-coding regulatory elements around an expression cassette
- Data: promoter and translation-initiation context
- Expected: annotation-aware explanation for expression differences

## Case V: Codon Usage Bias and Host Portability

- Focus: compare coding sequence suitability across host organisms
- Data: coding sequence and selected host preference
- Expected: codon-optimization output and host-portability discussion

## Cluster G: Data Fidelity And Interoperability

## Case I: DNA Container Roundtrip Validation

- Focus: verify that export and import preserve sequence identity
- Data: annotated record and Genome Forge DNA container
- Expected: clean roundtrip with preserved record properties

## Case J: AB1 Trace Alignment and Consensus Editing

- Focus: import a trace, align it, edit a base, and recompute consensus
- Data: AB1 trace or synthetic fallback trace plus reference sequence
- Expected: alignment summary and updated consensus sequence

## Case Y: Read Simulation and Coverage Planning

- Focus: think about how much sequence evidence is enough for confidence
- Data: target sequence and planned read placement
- Expected: reasoned coverage plan and confidence boundaries

## Case AE: Sequence Analytics Lens (GC, Skew, Complexity, Stop Density)

- Focus: use the analytics lens to locate problematic or interesting regions
- Data: long sequence window
- Expected: multi-track visualization with interpretable hotspot regions

## Case AF: Comparison Lens (Divergence + Confidence Hotspots)

- Focus: compare two related sequences and localize where they diverge most
- Data: aligned or alignable sequence pair
- Expected: divergence hotspot view with practical follow-up targets

## Case AG: Native .dna Import and Multi-Format Conversion Workflow

- Focus: move records between supported formats without losing key meaning
- Data: native `.dna` or Genome Forge DNA container plus export targets
- Expected: import success and multi-format conversion output

## Case AH: Chromatogram-First Sanger Review and Confidence Gating

- Focus: review raw-like peak evidence before trusting base calls
- Data: trace record with chromatogram output
- Expected: chromatogram window and confidence-based interpretation

## Case AI: Trace-Based Genotyping and Plasmid Verification

- Focus: call expected or unexpected sequence states from trace evidence
- Data: trace plus reference and expected base positions
- Expected: genotype calls, mismatch summary, and verification verdict

## Case AJ: BLAST-like Similarity Search for Identity, Origin, and Contamination

- Focus: identify what a sequence most resembles in a local reference panel
- Data: query sequence plus small local reference database
- Expected: ranked hits with identity, coverage, and score

## Case AK: Reference Element Auto-Flagging and siRNA Design/Mapping

- Focus: reuse saved element libraries and design RNAi targets
- Data: reference library plus sequence of interest
- Expected: flagged features, ranked siRNA candidates, and mapped binding sites

## Cluster H: Reproducibility, Governance, And Delivery

## Case L: Collaboration, Audit, and Review Governance

- Focus: create a workspace, assign roles, and run a review flow
- Data: saved project plus user role assignments
- Expected: audit entries and approved review state

## Case T: Batch Reproducibility and Parameter Locking

- Focus: repeat operations consistently across multiple inputs
- Data: several records and one locked parameter set
- Expected: reproducible batch outputs and history visibility

## Case AB: Reproducible Report Package

- Focus: save and reload a portable project/share package
- Data: saved project plus generated share bundle
- Expected: portable artifact that can be reopened and inspected

## Case AC: Parameter Sensitivity and Robustness Check

- Focus: compare how conclusions shift under reasonable parameter changes
- Data: one workflow rerun under a small sweep
- Expected: robustness notes and identification of fragile assumptions

## Case AD: End-to-End Release Checklist and Handoff

- Focus: validate the project at the release or handoff boundary
- Data: full repo plus validation commands
- Expected: green test status and handoff-ready project state
