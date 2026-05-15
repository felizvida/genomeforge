# Genome Forge Training Case Playbook

This playbook mirrors the tutorial exactly. Use it as the fast checklist after you have read the full narrative in the HTML/PDF version.

## Cluster A: Molecule Architecture and Restriction Logic

## Case A: Restriction Map for Cloning Entry Design

- Cluster: Molecule Architecture and Restriction Logic
- Focus: Which enzyme pair opens the vector cleanly without compromising the blue-white screening logic built around lacZ alpha?
- Records: pUC19_MCS, lacZ_alpha_fragment
- Workflow: Render the pUC19 map and compare unique restriction choices before adding a reporter insert.
- UI path: Map tab -> `Render the pUC19 map and compare unique restriction choices before adding a reporter insert.` -> Results plus the matching visualization panel
- APIs: /api/map, /api/digest
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case A --out ./tmp/genomeforge_case_a `
- Key expected signal: A circular map with the multiple-cloning site and reporter context clearly marked.
- Evidence/inference checkpoint: Unique cut sites are valuable because they open the vector once and only once.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case B: Methylation-Aware Digest Interpretation

- Cluster: Molecule Architecture and Restriction Logic
- Focus: Can a sequence that looks correct on paper still digest differently because the DNA was prepared in a methylating host?
- Records: pUC19_MCS
- Workflow: Compare standard digest output with methylation-aware digest logic on a real cloning vector motif set.
- UI path: Advanced tab -> `Compare standard digest output with methylation-aware digest logic on a real cloning vector motif set.` -> Results plus the matching visualization panel
- APIs: /api/digest-advanced
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case B --out ./tmp/genomeforge_case_b `
- Key expected signal: A digest report that lists both successful and blocked cut events.
- Evidence/inference checkpoint: If a predicted cut disappears only in the methylation-aware run, the enzyme is not suddenly “wrong”; the substrate context changed.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case C: Star Activity Risk Review

- Cluster: Molecule Architecture and Restriction Logic
- Focus: If reaction conditions get sloppy, where would near-miss cuts land and which of those cuts would actually hurt the experiment?
- Records: pUC19_MCS, lacZ_alpha_fragment
- Workflow: Scan relaxed-matching cut risk to understand how star activity can create off-target restriction events.
- UI path: Advanced tab -> `Scan relaxed-matching cut risk to understand how star activity can create off-target restriction events.` -> Results plus the matching visualization panel
- APIs: /api/star-activity-scan
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case C --out ./tmp/genomeforge_case_c `
- Key expected signal: A ranked list of possible star-activity sites and their mismatch burden.
- Evidence/inference checkpoint: A low total count is not automatically safe if one site lands in a fragile region.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case AN: Diagnostic Cutter Selection Between Related Constructs

- Cluster: Molecule Architecture and Restriction Logic
- Focus: If two constructs differ by only a small edit, which restriction enzyme gives the cleanest yes/no diagnostic digest?
- Records: pUC19_MCS
- Workflow: Compare a normal multiple-cloning-site sequence with a missing-site variant and choose enzymes that discriminate the two molecules.
- UI path: Advanced tab -> `Compare Restriction Sites` -> Diagnostic Restriction View
- APIs: /api/restriction-compare
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AN --out ./tmp/genomeforge_case_an `
- Key expected signal: A comparison table listing cut counts for both sequences.
- Evidence/inference checkpoint: The best diagnostic cutter is not necessarily the enzyme with the most sites; it is the enzyme whose pattern changes clearly between the alternatives.
- Bench decision: Choose the enzyme only if it creates a readable difference between the related molecules.
- Common caution: Do not prefer a cutter merely because it cuts often; prefer the cutter that answers the discrimination question cleanly.

## Case AO: Custom Ladder-Centric Digest Gel Planning

- Cluster: Molecule Architecture and Restriction Logic
- Focus: Will the gel ladder your lab actually uses make the diagnostic fragments easy to interpret?
- Records: pUC19_MCS
- Workflow: Define an in-house DNA ladder and render digest fragments against that ladder instead of a generic preset.
- UI path: Advanced tab -> `Digest Gel With Ladder` -> Results
- APIs: /api/gel-ladder-save, /api/gel-ladder-load, /api/digest-gel
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AO --out ./tmp/genomeforge_case_ao `
- Key expected signal: A saved custom ladder with named band sizes.
- Evidence/inference checkpoint: A custom ladder does not change the biology of the digest; it changes how confidently humans can read the output.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case U: k-mer Profile for Contamination Suspicion

- Cluster: Molecule Architecture and Restriction Logic
- Focus: Does the sequence composition look like one coherent construct, or does it hint that two familiar lab molecules were mixed together?
- Records: EGFP_CDS, mCherry_CDS, pUC19_MCS
- Workflow: Use motif/entity search patterns to ask whether a supposed single-template sample smells like a mixed cloning population.
- UI path: Search tab -> `Use motif/entity search patterns to ask whether a supposed single-template sample smells like a mixed cloning population.` -> Results plus the matching visualization panel
- APIs: /api/motif, /api/search-entities
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case U --out ./tmp/genomeforge_case_u `
- Key expected signal: A motif/entity hit list that can be compared with the expected construct identity.
- Evidence/inference checkpoint: If the feature hits are coherent with one construct, proceed to finer analysis.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Cluster B: Sequence Meaning and Functional Annotation

## Case D: Sequence Track and Translation Context

- Cluster: Sequence Meaning and Functional Annotation
- Focus: When you zoom in on a coding sequence, what exactly makes one nucleotide substitution harmless and another catastrophic?
- Records: EGFP_CDS
- Workflow: Inspect EGFP with sequence tracks so base coordinates, codons, amino acids, and features can be read together.
- UI path: Map tab -> `Inspect EGFP with sequence tracks so base coordinates, codons, amino acids, and features can be read together.` -> Results plus the matching visualization panel
- APIs: /api/sequence-tracks
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case D --out ./tmp/genomeforge_case_d `
- Key expected signal: A readable track that shows DNA letters, codons, amino acids, and annotations in register.
- Evidence/inference checkpoint: A change that stays within the same amino acid may still matter less than one that changes the protein sequence.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case AP: Text Map Reading for Dense Annotated Sequence

- Cluster: Sequence Meaning and Functional Annotation
- Focus: When a graphical map becomes too broad, can a text map help you inspect the exact bases, codons, and annotations without losing context?
- Records: EGFP_CDS
- Workflow: Render a text-map view that aligns sequence, translation, coordinates, and feature labels in a compact text-first representation.
- UI path: Map tab -> `Render Text Map` -> Text Map
- APIs: /api/text-map
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AP --out ./tmp/genomeforge_case_ap `
- Key expected signal: A rendered text map with visible coordinate blocks and sequence rows.
- Evidence/inference checkpoint: Text maps are not a replacement for visual maps; they are a different cognitive mode for close reading.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case M: ORF Scan and Coding Potential Triage

- Cluster: Sequence Meaning and Functional Annotation
- Focus: How do you tell whether a DNA segment should be treated like a protein-coding region or like genomic context that needs more annotation first?
- Records: BRAF_exon15_fragment, EGFP_CDS
- Workflow: Compare a clean coding sequence and a genomic fragment to learn what ORF scanning can and cannot tell you.
- UI path: ORF/Motif tab -> `Compare a clean coding sequence and a genomic fragment to learn what ORF scanning can and cannot tell you.` -> Results plus the matching visualization panel
- APIs: /api/orfs
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case M --out ./tmp/genomeforge_case_m `
- Key expected signal: A contrast between a sequence with obvious coding potential and one that needs context.
- Evidence/inference checkpoint: A single long ORF in the expected frame is a strong sign of coding structure, not absolute proof of biological function.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case P: Variant Annotation from Reference-Aligned Edits

- Cluster: Sequence Meaning and Functional Annotation
- Focus: How do you turn a one-codon difference into a biologically meaningful statement rather than just reporting a mismatch count?
- Records: EGFP_CDS, EGFP_Y67H_training_variant
- Workflow: Align a public reporter CDS to a derived chromophore variant and explain the difference in protein terms.
- UI path: Advanced tab -> `Align a public reporter CDS to a derived chromophore variant and explain the difference in protein terms.` -> Results plus the matching visualization panel
- APIs: /api/pairwise-align, /api/translated-features
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case P --out ./tmp/genomeforge_case_p `
- Key expected signal: A reference-vs-variant alignment with the changed codon localized clearly.
- Evidence/inference checkpoint: Count and consequence are different axes; one change can matter more than ten neutral ones.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case W: Protein Property Inference from Translation

- Cluster: Sequence Meaning and Functional Annotation
- Focus: What can you infer about a protein from sequence alone, and where do you have to stop and admit that cell context still matters?
- Records: EGFP_CDS, mCherry_CDS
- Workflow: Translate two real reporter proteins and compare what the sequence suggests about size, composition, and practical use.
- UI path: Advanced tab -> `Translate two real reporter proteins and compare what the sequence suggests about size, composition, and practical use.` -> Results plus the matching visualization panel
- APIs: /api/translate
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case W --out ./tmp/genomeforge_case_w `
- Key expected signal: A translated protein sequence and at least one simple composition or length comparison.
- Evidence/inference checkpoint: Relative length and motif composition can inform design, but they do not fully predict brightness, maturation, or toxicity.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Cluster C: Assay and Primer System Design

## Case E: Primer Design and Thermodynamic Screening

- Cluster: Assay and Primer System Design
- Focus: Can you design a primer pair that frames a clinically interesting genomic region without walking into obvious thermodynamic problems?
- Records: BRAF_exon15_fragment
- Workflow: Design primers around the BRAF hotspot region and screen them for temperature and composition sanity.
- UI path: Primer/PCR tab -> `Design primers around the BRAF hotspot region and screen them for temperature and composition sanity.` -> Results plus the matching visualization panel
- APIs: /api/primer-design
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case E --out ./tmp/genomeforge_case_e `
- Key expected signal: A primer pair with balanced Tm and acceptable GC content.
- Evidence/inference checkpoint: Matched Tm values matter because both primers need to anneal in the same PCR cycle window.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case F: Specificity Ranking with Virtual PCR/Gel

- Cluster: Assay and Primer System Design
- Focus: Which candidate primer pair is safest once you consider near-matches in the rest of the sequences that live on your bench?
- Records: EGFP_CDS, mCherry_CDS, BRAF_exon15_fragment
- Workflow: Rank candidate primer pairs against a realistic background panel and inspect the predicted gel outcome.
- UI path: Primer/PCR tab -> `Rank candidate primer pairs against a realistic background panel and inspect the predicted gel outcome.` -> Results plus the matching visualization panel
- APIs: /api/primer-specificity, /api/pcr, /api/gel-sim
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case F --out ./tmp/genomeforge_case_f `
- Key expected signal: A ranked candidate list with at least one rejected pair and one preferred pair.
- Evidence/inference checkpoint: Use the gel view to explain specificity, not just the score table.
- Bench decision: Use the primer pair only if specificity, size, Tm, and interpretation all support the assay goal.
- Common caution: A primer that binds somewhere is not necessarily a primer that produces an interpretable experiment.

## Case AL: Degenerate Primer Strategy for a Variant Family

- Cluster: Assay and Primer System Design
- Focus: How do you keep a PCR assay useful when the target family varies at one or two positions, or when your consensus still contains unresolved bases?
- Records: EGFP_CDS, EGFP_ambiguity_consensus_training, EGFP_Y67H_training_variant
- Workflow: Use an ambiguity-coded primer to keep one assay useful across a small reporter family and an uncertainty-bearing consensus sequence.
- UI path: Primer/PCR tab -> `Use an ambiguity-coded primer to keep one assay useful across a small reporter family and an uncertainty-bearing consensus sequence.` -> Results plus the matching visualization panel
- APIs: /api/primer-diagnostics, /api/primer-specificity, /api/pcr
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AL --out ./tmp/genomeforge_case_al `
- Key expected signal: A primer pair in which at least one primer contains IUPAC ambiguity symbols rather than only A/C/G/T.
- Evidence/inference checkpoint: A degenerate primer is valuable only if the ambiguous positions reflect real biological uncertainty or family diversity.
- Bench decision: Use the primer pair only if specificity, size, Tm, and interpretation all support the assay goal.
- Common caution: A primer that binds somewhere is not necessarily a primer that produces an interpretable experiment.

## Case Q: Multiplex PCR Panel Balancing

- Cluster: Assay and Primer System Design
- Focus: Can several assays be run together without one primer pair dominating or confusing the readout?
- Records: EGFP_CDS, mCherry_CDS, BRAF_exon15_fragment
- Workflow: Compare multiple assay targets and ask whether they can coexist in one panel without obvious conflict.
- UI path: Primer/PCR tab -> `Compare multiple assay targets and ask whether they can coexist in one panel without obvious conflict.` -> Results plus the matching visualization panel
- APIs: /api/primer-design, /api/primer-specificity, /api/pcr
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case Q --out ./tmp/genomeforge_case_q `
- Key expected signal: A panel plan that states which assays can coexist and which should be separated.
- Evidence/inference checkpoint: Panel design is a tradeoff between throughput and interpretability.
- Bench decision: Use the primer pair only if specificity, size, Tm, and interpretation all support the assay goal.
- Common caution: A primer that binds somewhere is not necessarily a primer that produces an interpretable experiment.

## Case AA: Positive and Negative Control Design

- Cluster: Assay and Primer System Design
- Focus: How do you design controls that let you distinguish “assay failed” from “biology absent”?
- Records: EGFP_CDS, mCherry_CDS, BRAF_exon15_fragment
- Workflow: Design an assay package that includes controls proving both signal presence and signal absence.
- UI path: Primer/PCR tab -> `Design an assay package that includes controls proving both signal presence and signal absence.` -> Results plus the matching visualization panel
- APIs: /api/primer-specificity, /api/pcr
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AA --out ./tmp/genomeforge_case_aa `
- Key expected signal: A written positive-control and negative-control plan tied to real records in the bundle.
- Evidence/inference checkpoint: Controls are part of the assay, not optional decorations.
- Bench decision: Use the primer pair only if specificity, size, Tm, and interpretation all support the assay goal.
- Common caution: A primer that binds somewhere is not necessarily a primer that produces an interpretable experiment.

## Cluster D: Assembly and Construct Validation

## Case G: Cloning Compatibility and Ligation Product Ranking

- Cluster: Assembly and Construct Validation
- Focus: If you pair a standard cloning vector with a reporter insert, what products are most likely and which ones should worry you?
- Records: pUC19_MCS, EGFP_CDS
- Workflow: Check whether the vector and insert support a coherent directional cloning plan and inspect likely ligation products.
- UI path: Advanced tab -> `Check whether the vector and insert support a coherent directional cloning plan and inspect likely ligation products.` -> Results plus the matching visualization panel
- APIs: /api/cloning-check, /api/ligation-sim
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case G --out ./tmp/genomeforge_case_g `
- Key expected signal: A compatibility verdict that explains whether the fragment ends and enzymes agree.
- Evidence/inference checkpoint: Compatibility is not just “yes/no”; it is also about the distribution of likely wrong answers.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case S: Circular Construct Integrity and Junction Validation

- Cluster: Assembly and Construct Validation
- Focus: After assembly, do the new junctions preserve the structure and reading logic you intended?
- Records: pUC19_MCS, EGFP_CDS
- Workflow: Validate a circularized construct by focusing on junctions, scars, and reading-frame continuity.
- UI path: Advanced tab -> `Validate a circularized construct by focusing on junctions, scars, and reading-frame continuity.` -> Results plus the matching visualization panel
- APIs: /api/gibson-assemble, /api/project-diff
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case S --out ./tmp/genomeforge_case_s `
- Key expected signal: A clear report for each assembly junction, including scar length and frame impact.
- Evidence/inference checkpoint: A construct can have the right parts but the wrong joins.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case Z: Multi-Trace Consensus for Final Construct Call

- Cluster: Assembly and Construct Validation
- Focus: When several sequencing reads exist for the same construct, how do you combine them into one decision rather than trusting the loudest trace?
- Records: EGFP_CDS
- Workflow: Combine multiple trace-derived views into one final verdict about a reporter construct.
- UI path: Trace tab -> `Combine multiple trace-derived views into one final verdict about a reporter construct.` -> Results plus the matching visualization panel
- APIs: /api/import-ab1, /api/trace-align, /api/trace-consensus
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case Z --out ./tmp/genomeforge_case_z `
- Key expected signal: A multi-trace summary with overlap or mismatch hotspots identified explicitly.
- Evidence/inference checkpoint: Agreement across independent traces raises confidence, especially when the same region is supported more than once.
- Bench decision: Accept the construct only where trace peaks support the called sequence at decision-critical bases.
- Common caution: A clean-looking consensus is not stronger than the raw trace evidence behind it.

## Cluster E: Comparative and Population-Level Reasoning

## Case H: MSA, Identity Heatmap, and Phylogeny

- Cluster: Comparative and Population-Level Reasoning
- Focus: How do related engineered proteins cluster, and what does that clustering tell you about reuse versus redesign?
- Records: EGFP_CDS, EGFP_Y67H_training_variant, EGFP_S204Y_training_variant, mCherry_CDS
- Workflow: Compare a small reporter family panel to see what is conserved, what is engineered, and what is genuinely distant.
- UI path: Advanced tab -> `Compare a small reporter family panel to see what is conserved, what is engineered, and what is genuinely distant.` -> Results plus the matching visualization panel
- APIs: /api/msa, /api/heatmap, /api/phylo
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case H --out ./tmp/genomeforge_case_h `
- Key expected signal: A multiple alignment that highlights both conserved backbone and engineered differences.
- Evidence/inference checkpoint: Use close clustering to justify localized interpretation, not blanket equivalence.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case N: GC Landscape and Repeat Fragility

- Cluster: Comparative and Population-Level Reasoning
- Focus: Where are the composition hotspots that make a seemingly simple sequence harder to amplify or synthesize?
- Records: mCherry_CDS, lacZ_alpha_fragment
- Workflow: Use analytics tracks to identify composition features that may complicate PCR, synthesis, or sequencing.
- UI path: Advanced tab -> `Use analytics tracks to identify composition features that may complicate PCR, synthesis, or sequencing.` -> Results plus the matching visualization panel
- APIs: /api/sequence-analytics
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case N --out ./tmp/genomeforge_case_n `
- Key expected signal: An analytics plot or table showing GC and complexity variation along the sequence.
- Evidence/inference checkpoint: Composition risk is contextual: a mild hotspot may be irrelevant for cloning but important for PCR primer placement.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case O: Homopolymer and Low-Complexity Risk Detection

- Cluster: Comparative and Population-Level Reasoning
- Focus: Do any parts of the sequence look too repetitive or too simple to trust without extra care?
- Records: lacZ_alpha_fragment, BRAF_exon15_fragment
- Workflow: Flag simple-sequence patches that often produce weak confidence in sequencing or synthesis workflows.
- UI path: Search tab -> `Flag simple-sequence patches that often produce weak confidence in sequencing or synthesis workflows.` -> Results plus the matching visualization panel
- APIs: /api/search-entities, /api/sequence-analytics
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case O --out ./tmp/genomeforge_case_o `
- Key expected signal: A list of low-complexity or homopolymer regions with coordinates.
- Evidence/inference checkpoint: Simple sequence is not automatically unusable; it just deserves less naive confidence.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case X: Motif Enrichment and Significance Framing

- Cluster: Comparative and Population-Level Reasoning
- Focus: When does a motif count reflect biology, and when does it simply reflect that one sequence was engineered to be motif-dense?
- Records: pUC19_MCS, EGFP_CDS, mCherry_CDS
- Workflow: Compare motif density across engineered vector DNA and reporter CDS records to learn when motif count is meaningful.
- UI path: Search tab -> `Compare motif density across engineered vector DNA and reporter CDS records to learn when motif count is meaningful.` -> Results plus the matching visualization panel
- APIs: /api/motif, /api/search-entities
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case X --out ./tmp/genomeforge_case_x `
- Key expected signal: A motif count table or hit map across at least two contrasting records.
- Evidence/inference checkpoint: Counts become meaningful when compared against sequence purpose, not in isolation.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Cluster F: Editing and Design for Intervention

## Case K: CRISPR Candidate and HDR Donor Design

- Cluster: Editing and Design for Intervention
- Focus: Can you move from a disease-relevant genomic fragment to a plausible editing plan without pretending that design scores are guarantees?
- Records: BRAF_exon15_fragment
- Workflow: Design guide RNAs and an HDR donor around a medically meaningful BRAF hotspot region.
- UI path: Advanced tab -> `Design guide RNAs and an HDR donor around a medically meaningful BRAF hotspot region.` -> Results plus the matching visualization panel
- APIs: /api/grna-design, /api/crispr-offtargets, /api/hdr-template
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case K --out ./tmp/genomeforge_case_k `
- Key expected signal: A shortlist of gRNA candidates near the intended edit window.
- Evidence/inference checkpoint: A guide closer to the edit is not automatically the best if the off-target profile is ugly.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case R: Promoter/RBS Context for Expression Tuning

- Cluster: Editing and Design for Intervention
- Focus: Why can two constructs with the same coding sequence express differently in cells or bacteria?
- Records: lacZ_alpha_fragment, EGFP_CDS
- Workflow: Use annotation and translation context to discuss why expression output depends on more than the CDS alone.
- UI path: Advanced tab -> `Use annotation and translation context to discuss why expression output depends on more than the CDS alone.` -> Results plus the matching visualization panel
- APIs: /api/auto-annotate, /api/sequence-tracks
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case R --out ./tmp/genomeforge_case_r `
- Key expected signal: A diagram or explanation that separates coding sequence from regulatory context.
- Evidence/inference checkpoint: When phenotype and sequence disagree, regulation is one of the first places to look.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case V: Codon Usage Bias and Host Portability

- Cluster: Editing and Design for Intervention
- Focus: If you move a gene between hosts, what sequence properties might become limiting even when the protein target stays the same?
- Records: EGFP_CDS, mCherry_CDS
- Workflow: Discuss how two common reporter CDS records might look to different host translation systems.
- UI path: Advanced tab -> `Discuss how two common reporter CDS records might look to different host translation systems.` -> Results plus the matching visualization panel
- APIs: /api/codon-optimize
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case V --out ./tmp/genomeforge_case_v `
- Key expected signal: A codon-optimization or codon-bias summary tied to a specific host scenario.
- Evidence/inference checkpoint: Codon changes can improve expression without changing the amino-acid sequence, but they can also affect RNA behavior and other features.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case AQ: Silent Restriction-Site Engineering

- Cluster: Editing and Design for Intervention
- Focus: Can you add a convenient screening site to a coding sequence while leaving the protein product unchanged?
- Records: EGFP_CDS
- Workflow: Search for synonymous coding-sequence edits that introduce or remove a restriction site without changing the translated protein.
- UI path: Advanced tab -> `Find Silent Restriction Sites` -> Silent Restriction Site View
- APIs: /api/silent-restriction-sites
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AQ --out ./tmp/genomeforge_case_aq `
- Key expected signal: A candidate list of synonymous edits grouped by enzyme and coordinate.
- Evidence/inference checkpoint: Silent means protein-preserving, not biologically irrelevant; codon usage, RNA structure, or regulatory motifs can still matter.
- Bench decision: Proceed only after confirming the edit preserves translation and does not create an unwanted local feature.
- Common caution: Silent means amino-acid-preserving, not automatically consequence-free.

## Cluster G: Data Fidelity and Interoperability

## Case I: DNA Container Roundtrip Validation

- Cluster: Data Fidelity and Interoperability
- Focus: Can you move records through a file format boundary without silently changing what the molecule means?
- Records: EGFP_CDS, mCherry_CDS, pUC19_MCS
- Workflow: Export and re-import multiple records to verify that file conversion preserves sequence identity and annotations.
- UI path: Advanced tab -> `Export and re-import multiple records to verify that file conversion preserves sequence identity and annotations.` -> Results plus the matching visualization panel
- APIs: /api/export-dna, /api/import-dna, /api/canonicalize-record
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case I --out ./tmp/genomeforge_case_i `
- Key expected signal: A before/after comparison showing that sequence identity survived the roundtrip.
- Evidence/inference checkpoint: Sequence identity alone is not enough for full interoperability.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case J: AB1 Trace Alignment and Consensus Editing

- Cluster: Data Fidelity and Interoperability
- Focus: How do raw sequencing traces become a confident construct call instead of just a noisy chromatogram picture?
- Records: EGFP_CDS
- Workflow: Import a Sanger-style trace, align it to EGFP, perform an edit, and recompute consensus.
- UI path: Trace tab -> `Import a Sanger-style trace, align it to EGFP, perform an edit, and recompute consensus.` -> Results plus the matching visualization panel
- APIs: /api/import-ab1, /api/trace-align, /api/trace-edit, /api/trace-consensus
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case J --out ./tmp/genomeforge_case_j `
- Key expected signal: A trace import with a visible chromatogram or summary.
- Evidence/inference checkpoint: If the called sequence and the raw peaks disagree, trust the evidence review over the first-pass label.
- Bench decision: Accept the construct only where trace peaks support the called sequence at decision-critical bases.
- Common caution: A clean-looking consensus is not stronger than the raw trace evidence behind it.

## Case Y: Read Simulation and Coverage Planning

- Cluster: Data Fidelity and Interoperability
- Focus: How much evidence is enough before you should trust a genotype or construct-verification conclusion?
- Records: BRAF_exon15_fragment, EGFP_CDS
- Workflow: Use realistic target regions to think about how much sequencing evidence is enough for a confident call.
- UI path: Advanced tab -> `Use realistic target regions to think about how much sequencing evidence is enough for a confident call.` -> Results plus the matching visualization panel
- APIs: /api/trace-consensus, /api/sequence-analytics
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case Y --out ./tmp/genomeforge_case_y `
- Key expected signal: A coverage or evidence plan tied to a real biological question.
- Evidence/inference checkpoint: Coverage is only meaningful relative to the decision you need to make.
- Bench decision: Accept the construct only where trace peaks support the called sequence at decision-critical bases.
- Common caution: A clean-looking consensus is not stronger than the raw trace evidence behind it.

## Case AE: Sequence Analytics Lens (GC, Skew, Complexity, Stop Density)

- Cluster: Data Fidelity and Interoperability
- Focus: What do multi-track analytics reveal that plain FASTA text hides?
- Records: EGFP_CDS, BRAF_exon15_fragment
- Workflow: Use the analytics lens on a clean CDS and a genomic fragment to see how sequence context changes interpretation.
- UI path: Advanced tab -> `Use the analytics lens on a clean CDS and a genomic fragment to see how sequence context changes interpretation.` -> Results plus the matching visualization panel
- APIs: /api/sequence-analytics
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AE --out ./tmp/genomeforge_case_ae `
- Key expected signal: A multi-track visualization with at least one biologically interpretable hotspot.
- Evidence/inference checkpoint: Use analytics as a triage map: where should you zoom in next?
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case AF: Comparison Lens (Divergence + Confidence Hotspots)

- Cluster: Data Fidelity and Interoperability
- Focus: How do you present a tiny but biologically meaningful difference in a way that a reviewer can understand at a glance?
- Records: EGFP_CDS, EGFP_Y67H_training_variant
- Workflow: Visualize where two nearly identical sequences diverge and decide whether the divergence matters.
- UI path: Advanced tab -> `Visualize where two nearly identical sequences diverge and decide whether the divergence matters.` -> Results plus the matching visualization panel
- APIs: /api/comparison-lens
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AF --out ./tmp/genomeforge_case_af `
- Key expected signal: A divergence view that localizes where the two records differ.
- Evidence/inference checkpoint: If all divergence is concentrated in one short interval, the biology probably is too.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case AG: Native .dna Import and Multi-Format Conversion Workflow

- Cluster: Data Fidelity and Interoperability
- Focus: Can one molecule remain understandable when it is exported into several popular sequence formats?
- Records: EGFP_CDS, pUC19_MCS
- Workflow: Demonstrate that a real record can move through multiple formats and come back interpretable.
- UI path: Advanced tab -> `Demonstrate that a real record can move through multiple formats and come back interpretable.` -> Results plus the matching visualization panel
- APIs: /api/import-dna, /api/convert, /api/canonicalize-record
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AG --out ./tmp/genomeforge_case_ag `
- Key expected signal: A multi-format export/import chain using the same underlying record.
- Evidence/inference checkpoint: Never assume a successful import preserved all the meaning you care about.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case AH: Chromatogram-First Sanger Review and Confidence Gating

- Cluster: Data Fidelity and Interoperability
- Focus: What does it look like when you review the measurement first and the called letters second?
- Records: EGFP_CDS
- Workflow: Start with the chromatogram itself before trusting the base calls.
- UI path: Trace/Interop tab -> `Trace Chromatogram` -> Sanger Chromatogram
- APIs: /api/import-ab1, /api/trace-chromatogram-svg
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AH --out ./tmp/genomeforge_case_ah `
- Key expected signal: A chromatogram view with at least one strong and one weak region called out.
- Evidence/inference checkpoint: Strong isolated peaks support confident calls; crowded or flat regions do not.
- Bench decision: Accept the construct only where trace peaks support the called sequence at decision-critical bases.
- Common caution: A clean-looking consensus is not stronger than the raw trace evidence behind it.

## Case AI: Trace-Based Genotyping and Plasmid Verification

- Cluster: Data Fidelity and Interoperability
- Focus: How do you turn trace evidence into a yes/no biological decision without pretending the trace is infallible?
- Records: BRAF_exon15_fragment, EGFP_CDS
- Workflow: Use trace evidence to make either a hotspot genotype call or a plasmid verification call.
- UI path: Trace tab -> `Use trace evidence to make either a hotspot genotype call or a plasmid verification call.` -> Results plus the matching visualization panel
- APIs: /api/trace-verify
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AI --out ./tmp/genomeforge_case_ai `
- Key expected signal: A verification report localizing any mismatches or confirming identity.
- Evidence/inference checkpoint: A zero-mismatch result is powerful only if the trace quality is also acceptable.
- Bench decision: Accept the construct only where trace peaks support the called sequence at decision-critical bases.
- Common caution: A clean-looking consensus is not stronger than the raw trace evidence behind it.

## Case AR: Linked Trace-to-Reference Navigation

- Cluster: Data Fidelity and Interoperability
- Focus: When a sequencing trace disagrees with the expected construct, how do you jump directly from the mismatch summary to the raw local evidence?
- Records: EGFP_CDS
- Workflow: Generate clickable trace/reference navigation anchors so each mismatch or low-confidence call can be inspected in sequence context.
- UI path: Trace/Interop tab -> `Linked Trace Alignment` -> Trace-to-Reference Links
- APIs: /api/import-ab1, /api/trace-alignment-links, /api/trace-chromatogram-svg
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AR --out ./tmp/genomeforge_case_ar `
- Key expected signal: A trace import followed by a linked alignment-navigation table.
- Evidence/inference checkpoint: Linked trace navigation is strongest when you use it to challenge, not merely confirm, the automatic call.
- Bench decision: Accept the construct only where trace peaks support the called sequence at decision-critical bases.
- Common caution: A clean-looking consensus is not stronger than the raw trace evidence behind it.

## Case AJ: BLAST-like Similarity Search for Identity, Origin, and Contamination

- Cluster: Data Fidelity and Interoperability
- Focus: If someone hands you a mystery sequence, which known molecule in your local panel does it most resemble?
- Records: EGFP_CDS, mCherry_CDS, lacZ_alpha_fragment, BRAF_exon15_fragment
- Workflow: Run local similarity search against a small real-world panel to identify the most likely source of an unknown sequence.
- UI path: Advanced tab -> `Run local similarity search against a small real-world panel to identify the most likely source of an unknown sequence.` -> Results plus the matching visualization panel
- APIs: /api/blast-search
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AJ --out ./tmp/genomeforge_case_aj `
- Key expected signal: A ranked hit list with identity and coverage, not just a single best match.
- Evidence/inference checkpoint: Full-length high-identity hits support strong identity claims.
- Bench decision: Use public-search hits to refine identity hypotheses, not to erase local coordinate context.
- Common caution: Top hit, high identity, and biological identity are related but not identical claims.

## Case AS: Selected-Sequence External BLAST Launch

- Cluster: Data Fidelity and Interoperability
- Focus: When local search says a sequence is interesting, how do you send exactly the selected region to a public reference search without losing coordinates or context?
- Records: EGFP_CDS
- Workflow: Package a selected sequence window as FASTA and launch or copy it for external NCBI and WormBase BLAST workflows.
- UI path: Advanced tab -> `Launch Selected Sequence Externally` -> External BLAST Launchpad
- APIs: /api/blast-launch
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AS --out ./tmp/genomeforge_case_as `
- Key expected signal: A copyable FASTA payload for the selected region, not the entire record by accident.
- Evidence/inference checkpoint: External BLAST results should refine local interpretation, not erase local context.
- Bench decision: Use public-search hits to refine identity hypotheses, not to erase local coordinate context.
- Common caution: Top hit, high identity, and biological identity are related but not identical claims.

## Case AK: Reference Element Auto-Flagging and siRNA Design/Mapping

- Cluster: Data Fidelity and Interoperability
- Focus: How do reusable sequence libraries turn repeated manual annotation into a faster and more consistent design workflow?
- Records: EGFP_CDS, mCherry_CDS
- Workflow: Reuse saved element libraries to auto-flag familiar sequence elements, then design and map siRNA candidates.
- UI path: Advanced tab -> `Reuse saved element libraries to auto-flag familiar sequence elements, then design and map siRNA candidates.` -> Results plus the matching visualization panel
- APIs: /api/reference-db-save, /api/reference-scan, /api/sirna-design, /api/sirna-map
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AK --out ./tmp/genomeforge_case_ak `
- Key expected signal: A reference-scan result showing which familiar elements were auto-flagged.
- Evidence/inference checkpoint: Auto-flagging is strongest when the reference database is curated and versioned.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case AM: Ambiguity-Aware Identity Search and Motif Rescue

- Cluster: Data Fidelity and Interoperability
- Focus: If a sequence contains unresolved positions, can you still recover its likely identity and use it responsibly instead of discarding it as “bad data”?
- Records: EGFP_CDS, EGFP_ambiguity_consensus_training, mCherry_CDS
- Workflow: Treat an ambiguity-bearing consensus record as a real query and verify that identity search and motif logic still recover the correct biological family.
- UI path: Advanced tab -> `Treat an ambiguity-bearing consensus record as a real query and verify that identity search and motif logic still recover the correct biological family.` -> Results plus the matching visualization panel
- APIs: /api/motif, /api/blast-search, /api/search-entities
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AM --out ./tmp/genomeforge_case_am `
- Key expected signal: A motif or similarity search in which an ambiguity-containing query still returns a biologically sensible top match.
- Evidence/inference checkpoint: Ambiguity-aware search should narrow the plausible identity space even when it cannot force every base to one final call.
- Bench decision: Use public-search hits to refine identity hypotheses, not to erase local coordinate context.
- Common caution: Top hit, high identity, and biological identity are related but not identical claims.

## Cluster H: Reproducibility, Governance, and Delivery

## Case L: Collaboration, Audit, and Review Governance

- Cluster: Reproducibility, Governance, and Delivery
- Focus: How do you make sequence work reviewable by another person instead of leaving it as personal screen state?
- Records: EGFP_CDS
- Workflow: Create a workspace, assign roles, and run a simple review flow on a saved construct project.
- UI path: Advanced tab -> `Create a workspace, assign roles, and run a simple review flow on a saved construct project.` -> Results plus the matching visualization panel
- APIs: /api/workspace-create, /api/project-permissions, /api/review-submit, /api/review-approve
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case L --out ./tmp/genomeforge_case_l `
- Key expected signal: A saved project with explicit role assignments and a traceable review event.
- Evidence/inference checkpoint: A sequence project that cannot be reviewed cleanly is harder to trust and harder to reuse.
- Bench decision: Treat the saved project as acceptable only if another person can reopen the data, evidence, and reasoning.
- Common caution: Screenshots are not reproducibility; saved state plus provenance is closer.

## Case T: Batch Reproducibility and Parameter Locking

- Cluster: Reproducibility, Governance, and Delivery
- Focus: How do you make sure that differences between records reflect biology instead of accidental parameter drift?
- Records: EGFP_CDS, mCherry_CDS, BRAF_exon15_fragment
- Workflow: Run the same logic across several records with a locked parameter set so outputs stay comparable.
- UI path: Advanced tab -> `Save Project` -> History Graph / Results
- APIs: /api/project-save, /api/sequence-analytics, /api/batch-digest
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case T --out ./tmp/genomeforge_case_t `
- Key expected signal: A batch run with identical settings applied to multiple records.
- Evidence/inference checkpoint: Locked parameters create fair comparisons.
- Bench decision: Treat the saved project as acceptable only if another person can reopen the data, evidence, and reasoning.
- Common caution: Screenshots are not reproducibility; saved state plus provenance is closer.

## Case AB: Reproducible Report Package

- Cluster: Reproducibility, Governance, and Delivery
- Focus: What does a handoff artifact look like when you want another person to inspect the same biological object, not just hear about it?
- Records: EGFP_CDS, pUC19_MCS
- Workflow: Package a saved project and a share bundle so another scientist can reopen the same analysis context.
- UI path: Advanced tab -> `Save Project` -> History Graph / Results
- APIs: /api/project-save, /api/share-create, /api/share-load
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AB --out ./tmp/genomeforge_case_ab `
- Key expected signal: A saved project plus a reloadable share bundle.
- Evidence/inference checkpoint: A package is only reproducible if it can be reopened independently of your current browser state.
- Bench decision: Treat the saved project as acceptable only if another person can reopen the data, evidence, and reasoning.
- Common caution: Screenshots are not reproducibility; saved state plus provenance is closer.

## Case AC: Parameter Sensitivity and Robustness Check

- Cluster: Reproducibility, Governance, and Delivery
- Focus: Would you reach the same biological conclusion if a reasonable analyst chose slightly different parameters?
- Records: BRAF_exon15_fragment, EGFP_CDS
- Workflow: Rerun a workflow under a small parameter sweep to see whether the biological conclusion is robust or fragile.
- UI path: Advanced tab -> `Rerun a workflow under a small parameter sweep to see whether the biological conclusion is robust or fragile.` -> Results plus the matching visualization panel
- APIs: /api/primer-design, /api/grna-design, /api/sequence-analytics
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AC --out ./tmp/genomeforge_case_ac `
- Key expected signal: A mini-sweep with at least one stable output and one potentially fragile output.
- Evidence/inference checkpoint: Stable outputs earn confidence; fragile outputs earn caution.
- Bench decision: Proceed when the output answers the biological question and the assumptions match the input data type.
- Common caution: Do not report the tool output as the conclusion; report the defensible biological interpretation.

## Case AD: End-to-End Release Checklist and Handoff

- Cluster: Reproducibility, Governance, and Delivery
- Focus: If you had to stop work today and let another person continue tomorrow, what would they need?
- Records: EGFP_CDS, mCherry_CDS, pUC19_MCS, BRAF_exon15_fragment
- Workflow: Treat the tutorial workspace like a releasable scientific software product and verify the handoff boundary.
- UI path: Advanced tab -> `Save Project` -> History Graph / Results
- APIs: /api/project-save, /api/share-create, /api/project-history-svg
- Extract bundle: `python3 docs/tutorial/datasets/extract_case_bundle.py --case AD --out ./tmp/genomeforge_case_ad `
- Key expected signal: A release-style checklist that covers data, docs, state, and verification.
- Evidence/inference checkpoint: The final deliverable is not the molecule alone; it is the reproducible workflow around the molecule.
- Bench decision: Treat the saved project as acceptable only if another person can reopen the data, evidence, and reasoning.
- Common caution: Screenshots are not reproducibility; saved state plus provenance is closer.
