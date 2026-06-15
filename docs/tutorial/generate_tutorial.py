#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import date
from html import escape
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[2]
TUTORIAL_DIR = ROOT / 'docs' / 'tutorial'
DATASET_DIR = TUTORIAL_DIR / 'datasets'
HTML_PATH = TUTORIAL_DIR / 'user_training_tutorial.html'
PLAYBOOK_PATH = DATASET_DIR / 'case_playbook.md'
DATASET_JSON_PATH = DATASET_DIR / 'training_real_world_dataset.json'
DATASET_README_PATH = DATASET_DIR / 'README.md'
FASTA_PATH = DATASET_DIR / 'training_real_world_sequences.fasta'
CASE_BUNDLES_DIR = DATASET_DIR / 'case_bundles'

TODAY = date.today().isoformat()
APP_VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
COPYRIGHT_YEAR = TODAY[:4]
REPO_URL = 'https://github.com/felizvida/genomeforge'
TUTORIAL_AUTHOR = 'Genome Forge contributors'
TUTORIAL_TITLE = 'Teach Yourself DNA Bioinformatics with Genome Forge'
TUTORIAL_SUBTITLE = 'A practical guide to sequence analysis, cloning design, molecular evidence, and reproducible lab workflows'

CLUSTERS = [
    {
        'id': 'A',
        'title': 'Molecule Architecture and Restriction Logic',
        'theme': 'How a DNA molecule is physically organized and where you can safely cut or modify it.',
        'figure': 'assets/01_map.svg',
        'caption': 'Circular and linear sequence views are most useful when you interpret them as future wet-lab decisions, not just graphics.',
    },
    {
        'id': 'B',
        'title': 'Sequence Meaning and Functional Annotation',
        'theme': 'How raw letters become genes, codons, proteins, and functional hypotheses.',
        'figure': 'assets/02_sequence_track.svg',
        'caption': 'Track views connect raw sequence, strand, feature, and codon logic in one place.',
    },
    {
        'id': 'C',
        'title': 'Assay and Primer System Design',
        'theme': 'How to design measurements that say something trustworthy about biology.',
        'figure': 'assets/05_star_activity.svg',
        'caption': 'Assay design is as much about avoiding false confidence as finding a candidate that “works.”',
    },
    {
        'id': 'D',
        'title': 'Assembly and Construct Validation',
        'theme': 'How to move from fragments and overlaps to a believable finished construct.',
        'figure': 'assets/06_ligation_products.svg',
        'caption': 'A plausible ligation or assembly plan should survive both sequence logic and biological interpretation.',
    },
    {
        'id': 'E',
        'title': 'Comparative and Population-Level Reasoning',
        'theme': 'How to compare related molecules, hotspot variants, and engineered families without overclaiming.',
        'figure': 'assets/03_msa_heatmap.svg',
        'caption': 'Heatmaps and alignments are only useful when you can explain what a difference means biologically.',
    },
    {
        'id': 'F',
        'title': 'Editing and Design for Intervention',
        'theme': 'How to turn sequence understanding into a purposeful intervention such as CRISPR, HDR, or expression tuning.',
        'figure': 'assets/05_star_activity.svg',
        'caption': 'Intervention design is a tradeoff problem: on-target success, off-target risk, and biological context all compete.',
    },
    {
        'id': 'G',
        'title': 'Data Fidelity and Interoperability',
        'theme': 'How to move between file formats, trace evidence, reference libraries, and similarity search without losing confidence.',
        'figure': 'assets/04_history_graph.svg',
        'caption': 'A reproducible bioinformatics workflow preserves both molecule state and the evidence that justified it.',
    },
    {
        'id': 'H',
        'title': 'Reproducibility, Governance, and Delivery',
        'theme': 'How to turn one-off sequence work into something another scientist can review, rerun, and trust.',
        'figure': 'assets/04_history_graph.svg',
        'caption': 'Good sequence work is a product, not just a result: it needs history, review, packaging, and handoff.',
    },
]

FEATURE_GALLERY = [
    {
        'title': 'Restriction-map reasoning',
        'file': 'assets/01_map.svg',
        'caption': 'A plasmid map is only useful when it helps you choose a safe cloning move. This view is strongest when paired with feature context and digest logic.',
    },
    {
        'title': 'Sequence-track thinking',
        'file': 'assets/02_sequence_track.svg',
        'caption': 'The whole point of a sequence-track view is to keep letters, codons, amino acids, and annotations in one frame of reference.',
    },
    {
        'title': 'Family-scale comparison',
        'file': 'assets/03_msa_heatmap.svg',
        'caption': 'Multiple alignment becomes biologically meaningful when you can point to a divergence hotspot and explain what the changed site may do.',
    },
    {
        'title': 'Provenance and history',
        'file': 'assets/04_history_graph.svg',
        'caption': 'Sequence work gains credibility when the molecular state and the decision trail stay attached to each other.',
    },
    {
        'title': 'Assay risk modeling',
        'file': 'assets/05_star_activity.svg',
        'caption': 'Good assay design is not just finding a candidate that works once. It is anticipating how the workflow can fail.',
    },
    {
        'title': 'Assembly visualization',
        'file': 'assets/06_ligation_products.svg',
        'caption': 'Assembly views help translate overlap logic into a believable final construct rather than a hand-wavy plan.',
    },
]

IUPAC_GUIDE = [
    ('A', 'A', 'Adenine only', 'Exact called base or exact assay requirement.'),
    ('C', 'C', 'Cytosine only', 'Exact called base or exact assay requirement.'),
    ('G', 'G', 'Guanine only', 'Exact called base or exact assay requirement.'),
    ('T', 'T', 'Thymine only', 'Exact called base or exact assay requirement.'),
    ('R', 'A or G', 'Purine', 'Useful when a site varies between adenine and guanine.'),
    ('Y', 'C or T', 'Pyrimidine', 'Common in mixed trace calls and degenerate primers.'),
    ('S', 'G or C', 'Strong pair', 'Both options make three hydrogen bonds to the complement.'),
    ('W', 'A or T', 'Weak pair', 'Both options make two hydrogen bonds to the complement.'),
    ('K', 'G or T', 'Keto', 'Used when the target family tolerates a purine/pyrimidine swap at one site.'),
    ('M', 'A or C', 'Amino', 'Useful for family-wide assay design.'),
    ('B', 'C or G or T', 'Not A', 'Represents uncertainty while still excluding one base.'),
    ('D', 'A or G or T', 'Not C', 'Represents uncertainty while still excluding one base.'),
    ('H', 'A or C or T', 'Not G', 'Represents uncertainty while still excluding one base.'),
    ('V', 'A or C or G', 'Not T', 'Represents uncertainty while still excluding one base.'),
    ('N', 'A or C or G or T', 'Any base', 'Used when the evidence does not justify a more specific call.'),
]

FLAGSHIP_SCREENSHOTS = {
    'A': {
        'file': 'assets/screenshots/flagship_case_a_map.png',
        'title': 'Restriction-map workflow in the live UI',
        'caption': 'Real UI screenshot from the bundled pUC19 MCS case. The map is rendered with a common cloning enzyme panel so you can see which sites are unique before choosing a directional cut strategy.',
    },
    'D': {
        'file': 'assets/screenshots/flagship_case_d_track.png',
        'title': 'Sequence-track workflow on EGFP',
        'caption': 'Real UI screenshot from the bundled EGFP CDS case. The track aligns nucleotide coordinates with frame-aware translation so codon logic is visible instead of implicit.',
    },
    'G': {
        'file': 'assets/screenshots/flagship_case_g_ligation.png',
        'title': 'Ligation and construct-planning workflow',
        'caption': 'Real UI screenshot of the ligation pathway view using tutorial vector/insert settings. This is the kind of panel you use to see whether the desired product dominates the byproduct space.',
    },
    'H': {
        'file': 'assets/screenshots/flagship_case_h_heatmap.png',
        'title': 'Reporter-family comparison workflow',
        'caption': 'Real UI screenshot from the reporter family alignment case. The identity heatmap helps you see that close engineering relatives cluster tightly while a more distant reporter separates cleanly.',
    },
    'AF': {
        'file': 'assets/screenshots/flagship_case_af_compare.png',
        'title': 'Comparison-lens workflow',
        'caption': 'Real UI screenshot from the EGFP-versus-variant comparison case. This lens is useful when two molecules are mostly identical and the interesting question is where the important divergence sits.',
    },
    'AH': {
        'file': 'assets/screenshots/flagship_case_ah_trace.png',
        'title': 'Chromatogram-first review workflow',
        'caption': 'Real UI screenshot of the Sanger-style chromatogram panel generated from the bundled EGFP trace example. It shows the workflow emphasis: inspect signal evidence before over-trusting the called sequence.',
    },
    'AJ': {
        'file': 'assets/screenshots/flagship_case_aj_blast.png',
        'title': 'BLAST-like identity search workflow',
        'caption': 'Real UI screenshot from the local similarity-search case using the tutorial panel of EGFP, mCherry, lacZ, and BRAF. This is the kind of view you use to ask where an unknown sequence most plausibly came from.',
    },
    'AL': {
        'file': 'assets/screenshots/flagship_case_al_degenerate_primers.png',
        'title': 'Degenerate-primer assay workflow',
        'caption': 'Real UI screenshot from the ambiguity-aware primer lesson. The primer fields intentionally contain IUPAC ambiguity symbols so one assay can tolerate a small reporter-family variation without hiding where uncertainty lives.',
    },
    'AM': {
        'file': 'assets/screenshots/flagship_case_am_ambiguity_search.png',
        'title': 'Ambiguity-aware identity search workflow',
        'caption': 'Real UI screenshot from the ambiguity-aware search lesson. The query itself carries unresolved positions, yet the search still recovers the correct reporter-family identity instead of treating the sequence as unusable.',
    },
    'AB': {
        'file': 'assets/screenshots/flagship_case_ab_history.png',
        'title': 'Project-history and reproducibility workflow',
        'caption': 'Real UI screenshot from a saved-project history case. This view matters because sequence work becomes more trustworthy when design state and revision history stay attached.',
    },
}

CONCEPT_ILLUSTRATIONS = {
    'AN': {
        'file': 'assets/concept_diagnostic_digest.svg',
        'title': 'Diagnostic digest concept map',
        'caption': 'This illustration shows why the restriction-comparison workflow matters biologically: a tiny sequence difference becomes a visible gel-band difference when the right cutter is chosen.',
    },
    'AQ': {
        'file': 'assets/concept_silent_site_engineering.svg',
        'title': 'Silent restriction-site engineering concept map',
        'caption': 'This illustration shows how genetic-code degeneracy lets a synonymous codon edit create a restriction site while preserving the protein sequence.',
    },
    'AR': {
        'file': 'assets/concept_trace_navigation.svg',
        'title': 'Linked trace review concept map',
        'caption': 'This illustration shows how linked trace navigation turns a mismatch row into a route back to chromatogram evidence instead of treating the table as the final verdict.',
    },
}

GLOSSARY_TERMS = {
    'amplicon': {
        'definition': 'A DNA segment produced by PCR.',
        'cs_analogy': 'A selected substring copied many times so it can be measured.',
        'why_it_matters': 'Amplicon size and specificity determine whether a gel, trace, or sequencing run answers the intended question.',
    },
    'CDS': {
        'definition': 'Coding sequence: the DNA interval that is translated into a protein.',
        'cs_analogy': 'The executable body of a function, excluding surrounding configuration.',
        'why_it_matters': 'Treating non-CDS DNA as CDS can create nonsense translations and misleading protein conclusions.',
    },
    'codon': {
        'definition': 'A three-base DNA word that specifies one amino acid or a stop signal.',
        'cs_analogy': 'A fixed-width instruction token read by the translation machine.',
        'why_it_matters': 'One inserted or deleted base shifts every downstream token and can destroy a protein.',
    },
    'consensus': {
        'definition': 'A best-supported sequence assembled from one or more reads or traces.',
        'cs_analogy': 'A merged result from multiple noisy observations.',
        'why_it_matters': 'Consensus calls should preserve uncertainty when evidence is ambiguous rather than inventing false precision.',
    },
    'frame': {
        'definition': 'The offset used to group DNA bases into codons.',
        'cs_analogy': 'The parser alignment for fixed-width tokens.',
        'why_it_matters': 'A correct sequence in the wrong frame can translate into a completely different protein.',
    },
    'methylation': {
        'definition': 'A chemical base modification that can block or alter enzyme cutting.',
        'cs_analogy': 'Hidden metadata attached to a character that changes how another program handles it.',
        'why_it_matters': 'A restriction site can exist in the text sequence but fail experimentally if methylation blocks the enzyme.',
    },
    'ORF': {
        'definition': 'Open reading frame: a stretch that can be translated without hitting a stop codon.',
        'cs_analogy': 'A candidate executable region with no early termination token.',
        'why_it_matters': 'ORFs are clues, not proof; biological context decides whether one is actually used.',
    },
    'restriction site': {
        'definition': 'A short DNA motif recognized and cut by a restriction enzyme.',
        'cs_analogy': 'A delimiter or cut marker embedded in a long string.',
        'why_it_matters': 'Restriction sites determine whether cloning, diagnostic digest, or screening plans are physically possible.',
    },
    'Sanger trace': {
        'definition': 'A chromatogram showing fluorescent peak evidence behind a called DNA sequence.',
        'cs_analogy': 'A debugger trace behind a summarized test result.',
        'why_it_matters': 'Base calls are interpretations of peaks; weak or mixed peaks should change confidence.',
    },
    'FASTQ': {
        'definition': 'A sequencing-read text format that stores bases and a quality character for each base.',
        'cs_analogy': 'A log file where every emitted token has an attached confidence score.',
        'why_it_matters': 'FASTQ lets you separate the called read sequence from the evidence quality behind each base.',
    },
    'coverage': {
        'definition': 'How many sequencing reads support each position in a reference sequence.',
        'cs_analogy': 'How many independent observations exercise a given line or branch.',
        'why_it_matters': 'A variant call at depth one is much weaker than the same call supported by multiple high-quality reads.',
    },
    'variant': {
        'definition': 'A base or sequence difference from the chosen reference.',
        'cs_analogy': 'A diff hunk relative to a known baseline.',
        'why_it_matters': 'Expected variants can confirm an edit; unexpected variants can reveal mistakes, contamination, or biology worth investigating.',
    },
    'silent mutation': {
        'definition': 'A DNA change that preserves the encoded amino acid.',
        'cs_analogy': 'A source-code rewrite that compiles to the same instruction.',
        'why_it_matters': 'Protein-preserving does not always mean biologically neutral because codon usage, RNA structure, or regulatory motifs can still shift.',
    },
    'topology': {
        'definition': 'Whether a DNA molecule is circular or linear.',
        'cs_analogy': 'A data structure boundary condition: wraparound exists for circular plasmids but not linear fragments.',
        'why_it_matters': 'Topology changes digest fragments, cloning interpretation, and map layout.',
    },
}

CHEAT_SHEETS = [
    {
        'title': 'Plasmid Map',
        'use_when': 'You need to decide where a construct can be cut, assembled, selected, or expressed.',
        'read_for': ['Topology', 'unique cutters', 'feature direction', 'antibiotic/selection markers'],
        'common_trap': 'Treating the map as decoration instead of an experimental plan.',
    },
    {
        'title': 'Reading Frame',
        'use_when': 'You are translating DNA, checking mutations, or designing silent edits.',
        'read_for': ['Start codon', 'codon triplets', 'stop codons', 'feature boundaries'],
        'common_trap': 'Starting translation one base too early or late and blaming the sequence.',
    },
    {
        'title': 'Diagnostic Digest',
        'use_when': 'You need an enzyme that distinguishes two related constructs or alleles.',
        'read_for': ['Cut count difference', 'fragment-size separation', 'single-site specificity', 'gel readability'],
        'common_trap': 'Choosing the enzyme with many cuts instead of the enzyme that answers the comparison question.',
    },
    {
        'title': 'Sanger Trace',
        'use_when': 'You are verifying a plasmid, genotype, or local edit.',
        'read_for': ['Peak quality', 'mixed bases', 'edge decay', 'alignment mismatch support'],
        'common_trap': 'Trusting the called letters without inspecting the chromatogram evidence.',
    },
    {
        'title': 'BLAST Result',
        'use_when': 'You need public-reference context for a selected sequence.',
        'read_for': ['Query coordinates', 'identity', 'coverage', 'database scope', 'runner-up hits'],
        'common_trap': 'Treating the top hit as identity proof without checking coverage and database context.',
    },
]

UI_GUIDES = [
    {
        'match_api': '/api/restriction-compare',
        'tab': 'Advanced',
        'fields': ['Sequence / FASTA / GenBank', 'Enzymes', 'Enzyme Set Name', 'Restriction Comparison / Diagnostic Cutters', 'Minimum Delta'],
        'button': 'Compare Restriction Sites',
        'panel': 'Diagnostic Restriction View',
        'sample': 'Use <code>BamHI,EcoRI,HindIII</code> and a related sequence in <code>Restriction Comparison / Diagnostic Cutters</code>.',
        'troubleshoot': 'If no candidates appear, lower <code>Minimum Delta</code> to 1 or add enzymes that recognize motifs present in only one construct.',
    },
    {
        'match_api': '/api/digest-gel',
        'tab': 'Advanced',
        'fields': ['Gel Band Sizes', 'User-Defined DNA Ladder', 'Enzymes', 'Enzyme Set Name'],
        'button': 'Digest Gel With Ladder',
        'panel': 'Results',
        'sample': 'Save the ladder first, then reuse its ladder name as the digest marker set.',
        'troubleshoot': 'If the gel is hard to interpret, add ladder bands near the expected fragment sizes or choose enzymes that separate fragments farther apart.',
    },
    {
        'match_api': '/api/text-map',
        'tab': 'Map',
        'fields': ['Track Start', 'Track End', 'Frame', 'Text Map Width'],
        'button': 'Render Text Map',
        'panel': 'Text Map',
        'sample': 'Start with width <code>80</code> and a short window such as <code>1..180</code> for readable line wrapping.',
        'troubleshoot': 'If translation looks wrong, check the frame selector before interpreting amino acids.',
    },
    {
        'match_api': '/api/silent-restriction-sites',
        'tab': 'Advanced',
        'fields': ['Frame', 'Enzymes', 'Enzyme Set Name', 'Silent Max Candidates'],
        'button': 'Find Silent Restriction Sites',
        'panel': 'Silent Restriction Site View',
        'sample': 'Use frame <code>1</code> for EGFP and a small enzyme set before expanding the search.',
        'troubleshoot': 'If all candidates are biologically awkward, narrow the enzyme list or inspect codon usage before adopting an edit.',
    },
    {
        'match_api': '/api/blast-launch',
        'tab': 'Advanced',
        'fields': ['BLAST Query Sequence', 'External BLAST Launch', 'BLAST Program', 'BLAST Database'],
        'button': 'Launch Selected Sequence Externally',
        'panel': 'External BLAST Launchpad',
        'sample': 'Enter a selected region or leave the query blank to use the current record sequence.',
        'troubleshoot': 'If provider interpretation feels inconsistent, confirm that the FASTA header contains the intended coordinates and that the database scope matches the organism question.',
    },
    {
        'match_api': '/api/annotation-transfer',
        'tab': 'Advanced',
        'fields': ['Similarity Annotation Transfer References', 'Annotation Transfer Identity', 'Annotation Transfer Coverage', 'Sequence / FASTA / GenBank'],
        'button': 'Transfer Annotations',
        'panel': 'Results',
        'sample': 'Paste an annotated EGFP reference record and use strict identity/coverage thresholds before adding transferred features.',
        'troubleshoot': 'If no features transfer, confirm the reference has feature locations and the target construct actually contains the referenced part.',
    },
    {
        'match_api': '/api/sanger-consensus',
        'tab': 'Trace/Interop',
        'fields': ['Reference Sequence For Trace Alignment', 'Sanger Consensus Reads', 'Trace Expected Bases', 'Minimum Called Percent'],
        'button': 'Multi-read Consensus',
        'panel': 'Results',
        'sample': 'Use multiple reads covering the expected edit and set expected bases only for positions with planned sequence changes.',
        'troubleshoot': 'If the verdict fails, inspect no-coverage genotype calls, unexpected variants, and mixed-position disagreements before changing the construct call.',
    },
    {
        'match_api': '/api/ngs-workflow-report',
        'tab': 'NGS Lite',
        'fields': ['FASTQ Reads', 'Reference For Read Mapping', 'Expected Variants', 'Adapter Sequence', 'Depth and variant thresholds'],
        'button': 'Workflow Report',
        'panel': 'NGS Lite Evidence Report',
        'sample': 'Use EGFP amplicon reads with one expected edit and one adapter-bearing read to inspect QC, trimming, coverage, and variants together.',
        'troubleshoot': 'If the verdict is review, inspect low-quality tails, zero-coverage regions, unexpected variants, and whether expected edits have enough read support.',
    },
    {
        'match_api': '/api/trace-alignment-links',
        'tab': 'Trace/Interop',
        'fields': ['Trace ID', 'Reference Sequence For Trace Alignment', 'Trace Window Start', 'Trace Window End'],
        'button': 'Linked Trace Alignment',
        'panel': 'Trace-to-Reference Links',
        'sample': 'Import or load a trace first, then keep the window narrow around the mismatch or verification region.',
        'troubleshoot': 'If rows do not link usefully, reduce the window and verify the trace reference sequence matches the intended construct orientation.',
    },
    {
        'match_api': '/api/trace-chromatogram-svg',
        'tab': 'Trace/Interop',
        'fields': ['Trace ID', 'Trace Window Start', 'Trace Window End'],
        'button': 'Trace Chromatogram',
        'panel': 'Sanger Chromatogram',
        'sample': 'Start with a high-confidence central window rather than the noisy trace edges.',
        'troubleshoot': 'If peaks look ambiguous, do not force a yes/no call; mark the region as needing repeat evidence.',
    },
    {
        'match_api': '/api/project-save',
        'tab': 'Advanced',
        'fields': ['Project Name', 'Workspace/Review fields if relevant'],
        'button': 'Save Project',
        'panel': 'History Graph / Results',
        'sample': 'Use a descriptive project name that encodes molecule, date, and decision state.',
        'troubleshoot': 'If a collaborator cannot reproduce the result, reload the saved project in a clean browser session and compare the history graph.',
    },
]

RECORDS = {
    'EGFP_CDS': {
        'type': 'public-source',
        'topology': 'linear',
        'sequence_ref': 'training_real_world_sequences.fasta:EGFP_CDS',
        'origin': 'Engineered fluorescent reporter derived from the Aequorea victoria GFP family.',
        'why_it_matters': 'EGFP is a canonical lab reporter: great for teaching translation, cloning, sequence verification, and how a few codons can change an optical phenotype.',
        'input_details': 'This is a protein-coding DNA sequence (CDS). The sequence is meant to be translated from the first base, so codon boundaries and reading frame matter immediately.',
        'fun_fact': 'A fluorescent protein is basically a self-reporting molecule: the sequence encodes the protein, and the folded protein creates its own chromophore.',
        'source_label': 'PubMed: enhanced GFP mutants overview',
        'source_url': 'https://pubmed.ncbi.nlm.nih.gov/9526659/',
        'suggested_features': [
            {'key': 'CDS', 'location': '1..720', 'qualifiers': {'label': 'EGFP', 'codon_start': '1'}},
            {'key': 'gene', 'location': '1..720', 'qualifiers': {'label': 'gfp'}},
        ],
    },
    'mCherry_CDS': {
        'type': 'public-source',
        'topology': 'linear',
        'sequence_ref': 'training_real_world_sequences.fasta:mCherry_CDS',
        'origin': 'Monomeric red fluorescent protein from the mFruit engineering lineage.',
        'why_it_matters': 'mCherry is a real-world counterexample to GFP: same broad job as a reporter, different sequence history, color, and engineering constraints.',
        'input_details': 'This is also a CDS, but it encodes a coral-derived red fluorescent protein rather than a GFP-family green reporter. That makes it useful for pairwise comparison and identity search.',
        'fun_fact': 'The reason mCherry mattered so much in cell biology is that it was engineered to behave as a monomer, which made protein fusions far easier to interpret.',
        'source_label': 'PubMed: A monomeric red fluorescent protein',
        'source_url': 'https://pubmed.ncbi.nlm.nih.gov/12060735/',
        'suggested_features': [
            {'key': 'CDS', 'location': '1..711', 'qualifiers': {'label': 'mCherry', 'codon_start': '1'}},
        ],
    },
    'pUC19_MCS': {
        'type': 'public-source',
        'topology': 'circular',
        'sequence_ref': 'training_real_world_sequences.fasta:pUC19_MCS',
        'origin': 'The pUC19 multiple-cloning site from one of the most widely used teaching and cloning vectors in molecular biology.',
        'why_it_matters': 'A dense multiple-cloning site is a perfect example of engineered sequence architecture: every base exists to make cloning more flexible.',
        'input_details': 'This sequence is short, circularly interpreted, and packed with restriction motifs. It is intentionally synthetic and engineered for manipulation rather than natural gene expression.',
        'fun_fact': 'The pUC19 MCS is tiny, but it changed day-to-day cloning because it made many enzyme choices available in one compact region.',
        'source_label': 'NCBI Nucleotide: pUC19 complete sequence',
        'source_url': 'https://www.ncbi.nlm.nih.gov/nuccore/M77789.2',
        'suggested_features': [
            {'key': 'misc_feature', 'location': '1..57', 'qualifiers': {'label': 'MCS'}},
        ],
    },
    'lacZ_alpha_fragment': {
        'type': 'public-source',
        'topology': 'linear',
        'sequence_ref': 'training_real_world_sequences.fasta:lacZ_alpha_fragment',
        'origin': 'lacZ alpha fragment from the classic blue-white screening system associated with cloning vectors such as pUC19.',
        'why_it_matters': 'This fragment is a perfect teaching example of phenotype-linked DNA: inserting the wrong thing into the wrong place changes colony color.',
        'input_details': 'The sequence is a cloning-era workhorse. It contains coding material, but many workflows care more about its role as a reporter module than as a standalone protein-coding fragment.',
        'fun_fact': 'Blue-white screening is a molecular biology hack built on protein complementation: the colony color is a proxy for whether the vector was disrupted.',
        'source_label': 'NCBI Nucleotide: pUC19 complete sequence',
        'source_url': 'https://www.ncbi.nlm.nih.gov/nuccore/M77789.2',
        'suggested_features': [
            {'key': 'CDS', 'location': '1..277', 'qualifiers': {'label': 'lacZ-alpha fragment', 'codon_start': '1'}},
        ],
    },
    'BRAF_exon15_fragment': {
        'type': 'public-source',
        'topology': 'linear',
        'sequence_ref': 'training_real_world_sequences.fasta:BRAF_exon15_fragment',
        'origin': 'A hotspot-rich fragment centered on human BRAF exon 15, the region associated with the famous V600 oncogenic mutation family.',
        'why_it_matters': 'This is the most medically consequential sequence in the training set. It is ideal for primer design, genotyping logic, CRISPR planning, and explaining why genomic DNA is not the same thing as a CDS.',
        'input_details': 'This is a genomic fragment, not a clean coding-sequence input. If you translate it naively, you hit stop codons because intron/exon context and strand assumptions matter.',
        'fun_fact': 'BRAF V600E became a textbook hotspot because one amino-acid change in a signaling kinase can rewire cell behavior so strongly that it becomes clinically actionable.',
        'source_label': 'NCBI Gene: BRAF (human)',
        'source_url': 'https://www.ncbi.nlm.nih.gov/gene/673',
        'suggested_features': [
            {'key': 'gene', 'location': '1..196', 'qualifiers': {'label': 'BRAF exon 15 training fragment'}},
        ],
    },
    'EGFP_Y67H_training_variant': {
        'type': 'derived-training',
        'topology': 'linear',
        'derived_from': 'EGFP_CDS',
        'edits': [
            {'start_1based': 199, 'end_1based': 201, 'replacement': 'CAC', 'label': 'Y67H-like chromophore edit'},
        ],
        'origin': 'Training derivative of EGFP that changes the aromatic residue in the chromophore-forming motif.',
        'why_it_matters': 'This is not a random mutation. It models the idea that one codon change near a chromophore can produce a large optical shift, which is a powerful lesson for variant interpretation.',
        'input_details': 'Because this record is derived from EGFP by a single codon change, it is excellent for pairwise alignment, amino-acid consequence analysis, and demonstrating how “small diff, big phenotype” problems happen in biology.',
        'fun_fact': 'Some of the most useful fluorescent protein families differ by only a handful of amino acids, yet those few edits can visibly change the color you see under the microscope.',
        'source_label': 'Derived from EGFP mutant logic described in GFP engineering literature',
        'source_url': 'https://pubmed.ncbi.nlm.nih.gov/9526659/',
        'suggested_features': [
            {'key': 'CDS', 'location': '1..720', 'qualifiers': {'label': 'EGFP Y67H-like variant', 'codon_start': '1'}},
        ],
    },
    'EGFP_S204Y_training_variant': {
        'type': 'derived-training',
        'topology': 'linear',
        'derived_from': 'EGFP_CDS',
        'edits': [
            {'start_1based': 610, 'end_1based': 612, 'replacement': 'TAC', 'label': 'S204Y-like aromatic packing edit'},
        ],
        'origin': 'Training derivative of EGFP that alters an aromatic-packing site near the chromophore environment.',
        'why_it_matters': 'It gives the tutorial a second closely related variant, which makes alignment, consensus, and comparison-lens examples far more realistic than comparing unrelated proteins only.',
        'input_details': 'Like the Y67H-like variant, this record is generated from a public-source EGFP backbone. The point is not to claim a specific commercial reagent but to give you a realistic engineering-style mutation to reason about.',
        'fun_fact': 'Spectral tuning in fluorescent proteins often happens because the local protein environment changes how the chromophore sees electrons, not because the whole protein is redesigned.',
        'source_label': 'Derived from EGFP engineering principles',
        'source_url': 'https://pubmed.ncbi.nlm.nih.gov/9526659/',
        'suggested_features': [
            {'key': 'CDS', 'location': '1..720', 'qualifiers': {'label': 'EGFP S204Y-like variant', 'codon_start': '1'}},
        ],
    },
    'EGFP_ambiguity_consensus_training': {
        'type': 'derived-training',
        'topology': 'linear',
        'derived_from': 'EGFP_CDS',
        'edits': [
            {'start_1based': 7, 'end_1based': 7, 'replacement': 'R', 'label': 'mixed A/G-like trace call'},
            {'start_1based': 10, 'end_1based': 10, 'replacement': 'Y', 'label': 'mixed C/T-like trace call'},
            {'start_1based': 67, 'end_1based': 67, 'replacement': 'N', 'label': 'low-confidence consensus position'},
        ],
        'origin': 'Training derivative of EGFP that uses IUPAC ambiguity symbols to mimic a consensus sequence assembled from uncertain or mixed evidence.',
        'why_it_matters': 'It teaches that uncertainty can be represented explicitly instead of being hidden behind a forced single-base call.',
        'input_details': 'This record is still an EGFP-like coding sequence, but a few positions are encoded as ambiguity symbols such as R, Y, and N. That means the sequence stands for a small set of plausible molecules rather than one exact DNA string.',
        'fun_fact': 'IUPAC ambiguity codes are basically a compact lossless summary of “here is what the data still allow” at a given position.',
        'source_label': 'Derived from EGFP_CDS for ambiguity-aware assay and search training',
        'source_url': 'https://pubmed.ncbi.nlm.nih.gov/9526659/',
        'suggested_features': [
            {'key': 'CDS', 'location': '1..720', 'qualifiers': {'label': 'EGFP ambiguity-aware consensus', 'codon_start': '1'}},
        ],
    },
}

RECORD_SETS = {
    'fluorescent_panel': ['EGFP_CDS', 'EGFP_Y67H_training_variant', 'EGFP_S204Y_training_variant', 'mCherry_CDS'],
    'cloning_panel': ['pUC19_MCS', 'lacZ_alpha_fragment', 'EGFP_CDS'],
    'oncology_panel': ['BRAF_exon15_fragment'],
    'roundtrip_panel': ['EGFP_CDS', 'mCherry_CDS', 'pUC19_MCS'],
    'ambiguity_panel': ['EGFP_CDS', 'EGFP_ambiguity_consensus_training', 'EGFP_Y67H_training_variant'],
}


def case(
    case_id: str,
    title: str,
    cluster: str,
    records: list[str],
    tab: str,
    workflow: str,
    apis: list[str],
    biological_question: str,
    data_details: str,
    biology: str,
    fun_fact: str,
    sample_result: dict,
    expected: list[str],
    interpretation: list[str],
    parameter_knob: str,
    starter_values: list[str] | None = None,
) -> dict:
    return {
        'id': case_id,
        'title': title,
        'cluster': cluster,
        'records': records,
        'tab': tab,
        'workflow': workflow,
        'apis': apis,
        'biological_question': biological_question,
        'data_details': data_details,
        'biology': biology,
        'fun_fact': fun_fact,
        'sample_result': sample_result,
        'expected': expected,
        'interpretation': interpretation,
        'parameter_knob': parameter_knob,
        'starter_values': starter_values or [],
    }


CASES = [
    case('A', 'Restriction Map for Cloning Entry Design', 'A', ['pUC19_MCS', 'lacZ_alpha_fragment'], 'Map', 'Render the pUC19 map and compare unique restriction choices before adding a reporter insert.', ['/api/map', '/api/digest'],
         'Which enzyme pair opens the vector cleanly without compromising the blue-white screening logic built around lacZ alpha?',
         'You are loading a real vector architecture rather than a random string. The pUC19 multiple-cloning site is deliberately dense with restriction motifs, and the adjacent lacZ alpha fragment is what gives the classic blue/white colony readout. Those two pieces together teach why a plasmid map is really an experimental design document.',
         'Restriction mapping matters because plasmid biology is modular. The MCS exists to be cut, but the neighboring reporter logic exists to be preserved or intentionally disrupted. A good cloning map therefore answers two questions at once: where can I cut, and what biological readout will survive afterward?',
         'The pUC19 multiple-cloning site is only a few dozen bases long, but it is one of the most recognizable pieces of engineered DNA in molecular biology.',
         {'unique_sites': ['EcoRI', 'BamHI', 'HindIII', 'XbaI', 'PstI', 'KpnI'], 'best_directional_pair': ['EcoRI', 'BamHI'], 'lacZ_alpha_screen_preserved_until_insert': True},
         ['A circular map with the multiple-cloning site and reporter context clearly marked.', 'A shortlist of unique cut sites or directional cut pairs that can linearize the vector safely.', 'A written decision explaining which enzyme choice best supports the intended cloning strategy.'],
         ['Unique cut sites are valuable because they open the vector once and only once.', 'A directional pair is stronger than two random unique sites because it helps enforce insert orientation.', 'If your chosen sites overlap a feature you depend on, the map is warning you before the bench can do it expensively.'],
         'changing the enzyme panel'),
    case('B', 'Methylation-Aware Digest Interpretation', 'A', ['pUC19_MCS'], 'Advanced', 'Compare standard digest output with methylation-aware digest logic on a real cloning vector motif set.', ['/api/digest-advanced'],
         'Can a sequence that looks correct on paper still digest differently because the DNA was prepared in a methylating host?',
         'The same pUC19-derived motif map is now interpreted with chemistry layered on top. The important input is not only the recognition site but also whether that site can be chemically masked by methylation, which is common in routine plasmid prep workflows.',
         'This case is one of the best ways to teach a computer scientist that biology has state beyond the ASCII sequence. The DNA letters are unchanged, yet the molecular behavior changes because an enzyme cannot access the site it expects.',
         'Many “mysterious digest failures” are actually host-state stories, not sequence-identity stories.',
         {'blocked_cuts': [{'enzyme': 'EcoRI', 'motif': 'GAATTC'}], 'remaining_visible_cuts': ['BamHI', 'HindIII'], 'status': 'revise host-or-enzyme plan'},
         ['A digest report that lists both successful and blocked cut events.', 'A fragment-length interpretation that changes after methylation is modeled.', 'A troubleshooting conclusion that explains whether the digest discrepancy is chemically plausible.'],
         ['If a predicted cut disappears only in the methylation-aware run, the enzyme is not suddenly “wrong”; the substrate context changed.', 'Blocked cuts near the cloning site can explain why a plasmid looks undigested or partially digested on a gel.', 'The practical fix is usually a different enzyme, a different host, or a different validation strategy.'],
         'changing the methylated motif list'),
    case('C', 'Star Activity Risk Review', 'A', ['pUC19_MCS', 'lacZ_alpha_fragment'], 'Advanced', 'Scan relaxed-matching cut risk to understand how star activity can create off-target restriction events.', ['/api/star-activity-scan'],
         'If reaction conditions get sloppy, where would near-miss cuts land and which of those cuts would actually hurt the experiment?',
         'The inputs are the same real cloning elements as Case A, but now the sequence is being treated under a relaxed specificity model. That lets you connect enzyme biochemistry to the spatial layout of engineered vector features.',
         'Star activity is a nice teaching bridge between exact pattern matching and biology under stress. Under non-ideal conditions, enzymes may behave like approximate matchers. The biologically important question is not just how many off-targets appear, but whether any land in irreplaceable regions.',
         'A single risky off-target cut inside a key feature matters more than a long list of harmless near-matches elsewhere.',
         {'star_hit_count': 4, 'highest_risk_region': 'lacZ_alpha boundary', 'recommended_response': 'tighten reaction conditions or switch enzyme'},
         ['A ranked list of possible star-activity sites and their mismatch burden.', 'A spatial interpretation of whether any near-miss cut touches essential cloning features.', 'A conservative recommendation for reducing digest risk.'],
         ['A low total count is not automatically safe if one site lands in a fragile region.', 'Star activity is a risk model, not proof that the event happened; treat it as an opportunity to design out uncertainty.', 'The strongest conclusion combines off-target count, target location, and how much the experimental readout depends on that region.'],
         'changing the mismatch tolerance'),
    case('AN', 'Diagnostic Cutter Selection Between Related Constructs', 'A', ['pUC19_MCS'], 'Advanced', 'Compare a normal multiple-cloning-site sequence with a missing-site variant and choose enzymes that discriminate the two molecules.', ['/api/restriction-compare'],
         'If two constructs differ by only a small edit, which restriction enzyme gives the cleanest yes/no diagnostic digest?',
         'This lesson starts with the pUC19 multiple-cloning site because it is intentionally rich in enzyme motifs, then asks what happens when one motif is missing from a related construct. That makes the workflow feel like a real colony-screening or allele-discrimination problem: the sequences are mostly the same, but one site should change the digest pattern.',
         'A diagnostic digest is a decision assay. You are not trying to characterize every base; you are trying to choose an enzyme whose cut-count difference turns a hidden sequence change into a visible banding difference. The computational move is to compare cut sites across two related sequences. The biological move is to ask whether that difference would be large and clean enough to trust at the bench.',
         'Many classic genotyping assays are clever because they convert an invisible one-base or small-motif change into a simple gel question: did this cutter cut or not?',
         {'sequence_a': 'pUC19_MCS', 'sequence_b': 'MCS variant lacking BamHI', 'diagnostic_enzyme': 'BamHI', 'cuts_in_a': 1, 'cuts_in_b': 0, 'interpretation': 'BamHI distinguishes the parent construct from the missing-site variant'},
         ['A comparison table listing cut counts for both sequences.', 'At least one diagnostic candidate where the cut count differs between the two records.', 'A written choice of enzyme and an expected banding difference for the diagnostic digest.'],
         ['The best diagnostic cutter is not necessarily the enzyme with the most sites; it is the enzyme whose pattern changes clearly between the alternatives.', 'A one-cut versus zero-cut difference is easy to reason about, but only if the resulting band sizes are resolvable.', 'Use this workflow before ordering a screen so your wet-lab assay tests the actual difference you care about.'],
         'changing the comparison sequence or minimum cut-count delta',
         starter_values=[
             'Sequence B example: remove the <code>GGATCC</code> BamHI motif from <code>pUC19_MCS</code>.',
             'Enzyme panel: <code>EcoRI,BamHI,HindIII,KpnI</code>',
             'Minimum delta: <code>1</code>',
         ]),
    case('AO', 'Custom Ladder-Centric Digest Gel Planning', 'A', ['pUC19_MCS'], 'Advanced', 'Define an in-house DNA ladder and render digest fragments against that ladder instead of a generic preset.', ['/api/gel-ladder-save', '/api/gel-ladder-load', '/api/digest-gel'],
         'Will the gel ladder your lab actually uses make the diagnostic fragments easy to interpret?',
         'The input molecule is short and enzyme-rich, but the real subject of the case is measurement context. A virtual digest is only useful if the marker lane resembles what the lab will actually load. Custom ladders let you model unusual in-house marker sets, truncated ladders, teaching-lab ladders, or vendor-specific bands.',
         'Gel interpretation is partly a visualization problem. Two digest plans can be chemically valid but differ dramatically in readability once the marker sizes and agarose resolution enter the picture. By saving a custom ladder, you make the simulated output speak the same visual language as the bench result.',
         'A ladder is a ruler made of DNA fragments. If you use the wrong ruler in planning, the experiment can be technically correct and still annoying to read.',
         {'custom_ladder': [10000, 8000, 5000, 3000, 1500, 750, 500, 250, 100], 'marker_set': 'tutorial_in_house_ladder', 'custom_marker': True, 'digest_enzymes': ['EcoRI', 'BamHI', 'HindIII'], 'planning_call': 'fragments are compared against the same ladder expected at the bench'},
         ['A saved custom ladder with named band sizes.', 'A digest-gel result whose marker lane reports that the custom marker set was used.', 'A conclusion about whether the diagnostic fragments are likely to separate well enough to interpret.'],
         ['A custom ladder does not change the biology of the digest; it changes how confidently humans can read the output.', 'If important fragments cluster between sparse ladder bands, the result may be harder to call than the enzyme logic suggests.', 'Use ladder-centric planning whenever the wet-lab readout will be a gel rather than a sequence trace.'],
         'changing the ladder band sizes or marker-set name',
         starter_values=[
             'Ladder name: <code>tutorial_in_house_ladder</code>',
             'Band sizes: <code>10000,8000,5000,3000,1500,750,500,250,100</code>',
             'Digest enzymes: <code>EcoRI,BamHI,HindIII</code>',
         ]),
    case('U', 'k-mer Profile for Contamination Suspicion', 'A', ['EGFP_CDS', 'mCherry_CDS', 'pUC19_MCS'], 'Search', 'Use motif/entity search patterns to ask whether a supposed single-template sample smells like a mixed cloning population.', ['/api/motif', '/api/search-entities'],
         'Does the sequence composition look like one coherent construct, or does it hint that two familiar lab molecules were mixed together?',
         'This case deliberately mixes a reporter-centric mental model with a vector-centric one. EGFP, mCherry, and pUC19 are all real lab molecules that often coexist on the same bench, which makes them realistic contamination suspects.',
         'Contamination is often easier to suspect at the pattern level than at the base-call level. If a sample contains motifs or feature signatures from mutually incompatible molecules, the safest interpretation is that the sample identity problem comes before any downstream design work.',
         'The most useful contamination clue is often not a mismatch; it is a motif or feature that simply should not coexist with the biology you thought you had.',
         {'unexpected_feature_hits': ['mCherry-like motif', 'pUC19-like restriction cluster'], 'contamination_hypothesis': 'mixed template or carryover plasmid', 'status': 'quarantine sample'},
         ['A motif/entity hit list that can be compared with the expected construct identity.', 'A short contamination hypothesis grounded in actual known molecules from the training panel.', 'A clear decision about whether to proceed or re-isolate the template.'],
         ['If the feature hits are coherent with one construct, proceed to finer analysis.', 'If the hit pattern combines signatures from incompatible molecules, do not over-interpret downstream outputs.', 'The cost of re-isolating a sample is usually much lower than the cost of trusting contaminated data.'],
         'changing the motif query or background panel'),
    case('D', 'Sequence Track and Translation Context', 'B', ['EGFP_CDS'], 'Map', 'Inspect EGFP with sequence tracks so base coordinates, codons, amino acids, and features can be read together.', ['/api/sequence-tracks'],
         'When you zoom in on a coding sequence, what exactly makes one nucleotide substitution harmless and another catastrophic?',
         'EGFP is ideal here because it is a clean CDS with a familiar biological output. Every base belongs to a protein-coding interval, so the main tutorial lesson is the relationship between nucleotide coordinates, codons, amino acids, and functional motifs.',
         'Translation context is where sequence analysis starts to feel biological rather than textual. A base is not just a character; it is part of a codon, which is part of a protein, which is part of a phenotype. That stacked interpretation is the point of a sequence track view.',
         'Once you see codons and amino acids aligned beneath the DNA, it becomes much easier to explain missense, synonymous, nonsense, and frameshift changes clearly.',
         {'frame': 1, 'visible_range_bp': '1..180', 'translated_window_aa': 60, 'dominant_feature': 'EGFP CDS'},
         ['A readable track that shows DNA letters, codons, amino acids, and annotations in register.', 'A consequence statement for at least one hypothetical or real base change.', 'A note about which positions are biologically sensitive and why.'],
         ['A change that stays within the same amino acid may still matter less than one that changes the protein sequence.', 'Frame is everything in coding DNA; off-by-one coordinate errors cascade into wrong protein logic.', 'Use the track view to narrate the result in plain language, not just to admire the color coding.'],
         'changing the visible window or frame'),
    case('AP', 'Text Map Reading for Dense Annotated Sequence', 'B', ['EGFP_CDS'], 'Map', 'Render a text-map view that aligns sequence, translation, coordinates, and feature labels in a compact text-first representation.', ['/api/text-map'],
         'When a graphical map becomes too broad, can a text map help you inspect the exact bases, codons, and annotations without losing context?',
         'EGFP is used here because it is a clean coding sequence with a known reading frame. The text map turns that record into a coordinate-aware reading exercise: letters, amino acids, and feature labels become rows in the same local window rather than separate panels.',
         'Text maps are especially useful for people who think like programmers. They make the sequence feel like an annotated source file: coordinates are line numbers, codons are tokens, and features are semantic overlays. The biological value is that you can inspect the exact bases behind a claim while keeping translation and annotation visible.',
         'A good text map is almost a bilingual edition of DNA: one line is nucleotide text, another is amino-acid meaning, and the annotations tell you why the region matters.',
         {'record': 'EGFP_CDS', 'window': '1..180', 'frame': 1, 'text_map_contains': ['coordinates', 'DNA sequence', 'frame-1 translation', 'EGFP feature label'], 'interpretation': 'the same local region can be read as bases, codons, and biological feature context'},
         ['A rendered text map with visible coordinate blocks and sequence rows.', 'A translation row in the expected frame for the EGFP CDS window.', 'Feature labels aligned to the same local coordinate system as the sequence text.'],
         ['Text maps are not a replacement for visual maps; they are a different cognitive mode for close reading.', 'If a proposed edit is hard to explain in the text map, you may not yet understand its coordinate or frame consequences.', 'Use text maps when exact local context matters more than whole-plasmid shape.'],
         'changing the start/end window or translation frame',
         starter_values=[
             'Window: <code>1..180</code>',
             'Width: <code>90</code>',
             'Frame: <code>1</code>',
         ]),
    case('M', 'ORF Scan and Coding Potential Triage', 'B', ['BRAF_exon15_fragment', 'EGFP_CDS'], 'ORF/Motif', 'Compare a clean coding sequence and a genomic fragment to learn what ORF scanning can and cannot tell you.', ['/api/orfs'],
         'How do you tell whether a DNA segment should be treated like a protein-coding region or like genomic context that needs more annotation first?',
         'The two records in this case are intentionally different. EGFP is a textbook CDS. The BRAF fragment is genomic and hotspot-rich, which means naive translation generates stop codons. That contrast teaches why ORF scans are triage tools, not oracles.',
         'This is a high-value lesson for engineers: a tool can be internally correct and still answer the wrong biological question if the input type is misunderstood. ORFs are plausible coding intervals, not proof that the DNA came from a translated transcript.',
         'The BRAF fragment is useful precisely because it fails the “clean ORF” expectation. That failure is teaching you something true about the data type.',
         {'EGFP_orf_count': 1, 'EGFP_longest_orf_aa': 239, 'BRAF_fragment_orf_count': 2, 'BRAF_interpretation': 'genomic fragment, not standalone CDS'},
         ['A contrast between a sequence with obvious coding potential and one that needs context.', 'An explanation of why stop codons appear in the genomic fragment without implying the data are wrong.', 'A triage decision: treat as CDS-like, genomic-context, or needs more annotation.'],
         ['A single long ORF in the expected frame is a strong sign of coding structure, not absolute proof of biological function.', 'Multiple short ORFs in a genomic fragment usually mean you are translating the wrong conceptual object.', 'The output should change what you do next: translate, annotate further, or align to a reference transcript.'],
         'changing the minimum ORF length'),
    case('P', 'Variant Annotation from Reference-Aligned Edits', 'B', ['EGFP_CDS', 'EGFP_Y67H_training_variant'], 'Advanced', 'Align a public reporter CDS to a derived chromophore variant and explain the difference in protein terms.', ['/api/pairwise-align', '/api/translated-features'],
         'How do you turn a one-codon difference into a biologically meaningful statement rather than just reporting a mismatch count?',
         'The input pair is intentionally gentle: a real EGFP sequence and a one-codon training derivative that changes a chromophore residue. Because the background is almost identical, the interpretation can focus on effect rather than search difficulty.',
         'Variant annotation is where sequence diff becomes biological reasoning. In this example, one codon change is easy to describe computationally, but the real point is that a small DNA edit can substantially change fluorescence behavior because it lands in a structurally privileged site.',
         '“Only one codon changed” is not a reassuring statement if that codon sits inside the business end of the molecule.',
         {'nucleotide_changes': 1, 'codon_change': 'TAC -> CAC', 'protein_change': 'Y67H-like', 'impact_class': 'missense, chromophore-adjacent'},
         ['A reference-vs-variant alignment with the changed codon localized clearly.', 'A protein-level consequence statement rather than a nucleotide-only diff.', 'A short explanation of why the changed site is worth caring about biologically.'],
         ['Count and consequence are different axes; one change can matter more than ten neutral ones.', 'If the changed codon sits in a known structural or functional motif, say so explicitly.', 'Strong annotation ends with a hypothesis about phenotype, not just a coordinate.'],
         'changing the reference/variant pair'),
    case('W', 'Protein Property Inference from Translation', 'B', ['EGFP_CDS', 'mCherry_CDS'], 'Advanced', 'Translate two real reporter proteins and compare what the sequence suggests about size, composition, and practical use.', ['/api/translate'],
         'What can you infer about a protein from sequence alone, and where do you have to stop and admit that cell context still matters?',
         'EGFP and mCherry are perfect for this because they are used for the same broad purpose but arise from different engineering histories. Translating them side by side shows how protein length, composition, and conserved motifs can support useful but limited inference.',
         'Protein-property inference is about turning sequence into hypotheses: relative length, likely folding burden, presence of aromatic or charged segments, and the kinds of features that might influence fluorescence or fusion behavior. It is not a replacement for experimental characterization.',
         'Fluorescent proteins are great teaching tools because their phenotype is visible, but the visible color still emerges from a long chain of sequence-to-structure-to-chemistry logic.',
         {'EGFP_length_aa': 239, 'mCherry_length_aa': 236, 'shared_use_case': 'fluorescent reporting', 'interpretation': 'similar application, different sequence families'},
         ['A translated protein sequence and at least one simple composition or length comparison.', 'A practical hypothesis about how the protein might behave as a reporter or fusion tag.', 'A boundary statement explaining what sequence alone cannot prove.'],
         ['Relative length and motif composition can inform design, but they do not fully predict brightness, maturation, or toxicity.', 'A useful tutorial answer sounds like “this sequence suggests X, but we still need Y to be sure.”', 'Whenever possible, connect the protein-level claim back to the actual reporter phenotype people care about in the lab.'],
         'changing which translated record you compare'),
    case('E', 'Primer Design and Thermodynamic Screening', 'C', ['BRAF_exon15_fragment'], 'Primer/PCR', 'Design primers around the BRAF hotspot region and screen them for temperature and composition sanity.', ['/api/primer-design'],
         'Can you design a primer pair that frames a clinically interesting genomic region without walking into obvious thermodynamic problems?',
         'The BRAF exon 15 fragment is real, short enough for tutorial work, and biologically meaningful because many sequencing and genotyping assays target the V600 hotspot neighborhood. That makes the primer choices easier to care about.',
         'Primer design is a statistical control problem disguised as a string problem. You want oligos that bind where you mean, with similar melting behavior, reasonable GC composition, and minimal self-complementarity. Every one of those constraints exists because polymerases and DNA hybridization are physical processes, not abstract matches.',
         'A primer pair that looks elegant in FASTA text can still fail because DNA strands form structures and compete for binding.',
         {'target_window_bp': 'around exon 15 hotspot', 'best_pair_tm_c': [60.8, 61.2], 'gc_pct_range': [47.6, 52.4], 'status': 'candidate primer pair selected'},
         ['A primer pair with balanced Tm and acceptable GC content.', 'A note about any hairpin or dimer liabilities that need monitoring.', 'A clear statement of what region the assay will amplify and why that region matters biologically.'],
         ['Matched Tm values matter because both primers need to anneal in the same PCR cycle window.', 'A primer pair is only useful if its amplicon captures the biology you actually care about—in this case, hotspot-rich BRAF sequence.', 'Design is not finished when the tool outputs two strings; it is finished when you can defend the pair scientifically.'],
         'changing the amplicon window or primer length'),
    case('F', 'Specificity Ranking with Virtual PCR/Gel', 'C', ['EGFP_CDS', 'mCherry_CDS', 'BRAF_exon15_fragment'], 'Primer/PCR', 'Rank candidate primer pairs against a realistic background panel and inspect the predicted gel outcome.', ['/api/primer-specificity', '/api/pcr', '/api/gel-sim'],
         'Which candidate primer pair is safest once you consider near-matches in the rest of the sequences that live on your bench?',
         'This case uses three real records that make a realistic small background panel: two reporter genes and one oncogene fragment. In practice, background panels matter because labs reuse templates constantly and cross-reactivity is common.',
         'Virtual PCR is valuable because it converts abstract specificity scores into something a bench scientist immediately understands: extra bands, wrong-size bands, or a clean expected product. It turns computational screening into an experimental expectation.',
         'A clean gel simulation is a communication tool: it helps a junior scientist understand why one primer pair is risky without making them parse thermodynamic tables first.',
         {'ranked_pair': 'EGFP_pair_1', 'predicted_product_bp': 461, 'off_target_bands': 0, 'gel_call': 'single dominant band'},
         ['A ranked candidate list with at least one rejected pair and one preferred pair.', 'A predicted gel pattern that explains the ranking in experimental terms.', 'A final recommendation that ties specificity back to the intended assay.'],
         ['Use the gel view to explain specificity, not just the score table.', 'A pair with a slightly lower score but cleaner off-target profile may still be the better scientific choice.', 'The winning pair is the one you would be comfortable handing to someone else in the lab.'],
         'changing the background record panel'),
    case('AL', 'Degenerate Primer Strategy for a Variant Family', 'C', ['EGFP_CDS', 'EGFP_ambiguity_consensus_training', 'EGFP_Y67H_training_variant'], 'Primer/PCR', 'Use an ambiguity-coded primer to keep one assay useful across a small reporter family and an uncertainty-bearing consensus sequence.', ['/api/primer-diagnostics', '/api/primer-specificity', '/api/pcr'],
         'How do you keep a PCR assay useful when the target family varies at one or two positions, or when your consensus still contains unresolved bases?',
         'This case uses one clean reporter CDS, one biologically meaningful single-codon variant, and one uncertainty-bearing consensus sequence. That combination mirrors a real workflow in which a lab wants one assay that still works across a clone family, a mutagenesis panel, or a partially resolved sequencing result.',
         'Degenerate primers are a controlled way to encode biological uncertainty into an assay design. Instead of pretending every member of a target family is identical, you let the primer represent a small allowed set of bases at carefully chosen positions. Computationally, that means the primer is no longer one string. Biologically, it means one assay can cover a family without lying about where the family differs.',
         'A degenerate primer is a compact statement that says, “I know exactly where uncertainty lives, and I am designing around it rather than ignoring it.”',
         {'forward_primer': 'ATGGTGRGYAAGGGCGAGGA', 'reverse_primer': 'CTTGTACAGCTCGTCCATGC', 'background_records': 3, 'predicted_products': [{'record': 'EGFP_CDS', 'size_bp': 119}, {'record': 'EGFP_ambiguity_consensus_training', 'size_bp': 119}, {'record': 'EGFP_Y67H_training_variant', 'size_bp': 119}], 'interpretation': 'one family-tolerant assay retained while off-target risk stays low in the reporter panel'},
         ['A primer pair in which at least one primer contains IUPAC ambiguity symbols rather than only A/C/G/T.', 'A specificity report showing that the intended family members still amplify while unrelated products remain limited.', 'A justification for why the ambiguity positions were placed where they were, rather than scattered arbitrarily.'],
         ['A degenerate primer is valuable only if the ambiguous positions reflect real biological uncertainty or family diversity.', 'If a primer becomes too degenerate, you gain family coverage but may lose specificity or synthesis practicality.', 'The best outcome is not “maximum ambiguity”; it is the smallest ambiguity set that still captures the biological family you care about.'],
         'changing the ambiguous positions or the background family',
         starter_values=[
             'Forward primer seed: <code>ATGGTGRGYAAGGGCGAGGA</code>',
             'Reverse primer seed: <code>CTTGTACAGCTCGTCCATGC</code>',
             'Background panel: <code>EGFP_CDS, EGFP_ambiguity_consensus_training, EGFP_Y67H_training_variant</code>',
         ]),
    case('Q', 'Multiplex PCR Panel Balancing', 'C', ['EGFP_CDS', 'mCherry_CDS', 'BRAF_exon15_fragment'], 'Primer/PCR', 'Compare multiple assay targets and ask whether they can coexist in one panel without obvious conflict.', ['/api/primer-design', '/api/primer-specificity', '/api/pcr'],
         'Can several assays be run together without one primer pair dominating or confusing the readout?',
         'Multiplex design is where assay design becomes systems design. The same three tutorial records now behave like a miniature panel: reporter control, second reporter, and clinically interesting target. You are no longer optimizing one pair in isolation.',
         'Biologically, multiplexing matters because samples and reagents are finite. But multiplex success depends on compatible primer temperatures, separable product sizes, and low cross-talk. This is a good example of engineering constraints arising directly from molecular competition.',
         'When a multiplex assay works, it feels efficient; when it fails, it often fails in ways that are hard to interpret unless the panel was designed carefully from the start.',
         {'panel_targets': 3, 'recommended_layout': ['EGFP control', 'mCherry control', 'BRAF amplicon'], 'risk_note': 'separate amplicon sizes by >100 bp'},
         ['A panel plan that states which assays can coexist and which should be separated.', 'A size-spacing or Tm-spacing rationale for the panel design.', 'A decision about whether multiplexing is justified or whether singleplex is safer.'],
         ['Panel design is a tradeoff between throughput and interpretability.', 'If two amplicons are too close in size or two primer pairs compete strongly, you lose the main benefit of multiplexing: clean interpretation.', 'The safest multiplex panel is the one that still makes sense when something goes slightly wrong.'],
         'changing the primer pool or target combination'),
    case('AA', 'Positive and Negative Control Design', 'C', ['EGFP_CDS', 'mCherry_CDS', 'BRAF_exon15_fragment'], 'Primer/PCR', 'Design an assay package that includes controls proving both signal presence and signal absence.', ['/api/primer-specificity', '/api/pcr'],
         'How do you design controls that let you distinguish “assay failed” from “biology absent”?',
         'The real-world records make control design concrete. EGFP and mCherry behave like easy positives or orthogonal negatives depending on the assay, while BRAF gives you a genomically relevant target to frame the main test.',
         'Control design is bioinformatics quality assurance. A positive control proves the chemistry and analysis pipeline can detect a known target. A negative control proves that the same pipeline does not hallucinate signal where it should not.',
         'The best controls are boring in the best possible way: they make the interpretation unambiguous.',
         {'positive_control': 'EGFP amplicon', 'negative_control': 'mCherry background for EGFP assay', 'decision_rule': 'trust call only if controls behave as expected'},
         ['A written positive-control and negative-control plan tied to real records in the bundle.', 'Expected control outcomes that could be checked by PCR, gel, or trace.', 'A simple rule for when the assay run should be accepted or rejected.'],
         ['Controls are part of the assay, not optional decorations.', 'A main result without controls has lower value than a boring run with clear controls.', 'Write the decision rule in advance so you do not move the goalposts after the experiment.'],
         'changing which record acts as the control'),
    case('G', 'Cloning Compatibility and Ligation Product Ranking', 'D', ['pUC19_MCS', 'EGFP_CDS'], 'Advanced', 'Check whether the vector and insert support a coherent directional cloning plan and inspect likely ligation products.', ['/api/cloning-check', '/api/ligation-sim'],
         'If you pair a standard cloning vector with a reporter insert, what products are most likely and which ones should worry you?',
         'This uses a real vector backbone logic plus a real reporter CDS. The point is to translate compatibility from enzyme names into actual product architecture: correct insert, flipped insert, vector self-ligation, or multi-insert byproducts.',
         'Assembly planning is a graph problem with a biological cost function. Multiple products may be chemically possible, but only one or two are biologically useful. The tutorial goal is to teach you to read that distinction before doing the ligation.',
         'A cloning simulation is most helpful when it tells you what wrong products to expect, because that is what saves time on the bench.',
         {'compatible': True, 'top_product': 'vector+EGFP directional insert', 'byproduct_examples': ['self-ligated vector', 'reverse-orientation insert']},
         ['A compatibility verdict that explains whether the fragment ends and enzymes agree.', 'A ranked product list with at least one plausible byproduct.', 'A short note on how you would validate the top product experimentally.'],
         ['Compatibility is not just “yes/no”; it is also about the distribution of likely wrong answers.', 'A design that produces one dominant useful product and several weak byproducts is stronger than a design with many equal possibilities.', 'Use the ranked product list to decide which colony-screening strategy makes sense afterward.'],
         'changing the enzyme pair or overlap rule'),
    case('S', 'Circular Construct Integrity and Junction Validation', 'D', ['pUC19_MCS', 'EGFP_CDS'], 'Advanced', 'Validate a circularized construct by focusing on junctions, scars, and reading-frame continuity.', ['/api/gibson-assemble', '/api/project-diff'],
         'After assembly, do the new junctions preserve the structure and reading logic you intended?',
         'The same vector+reporter system now becomes a finished construct problem. Junctions are where cloning plans usually fail: scars appear, frames shift, or regulatory context is disrupted in ways the raw map did not make obvious.',
         'Junction validation is biologically central because most engineered molecules are mostly “known good” plus a few critical joins. Those joins are where function is created or destroyed. If you cannot explain the junction, you do not understand the construct.',
         'A plasmid is often won or lost at only a handful of bases: the junctions carry disproportionate functional meaning.',
         {'junctions_checked': 2, 'frame_preserved': True, 'scar_bp': 0, 'status': 'construct architecture consistent'},
         ['A clear report for each assembly junction, including scar length and frame impact.', 'A statement about whether circular continuity preserves the intended construct logic.', 'A validation plan for confirming the junctions experimentally.'],
         ['A construct can have the right parts but the wrong joins.', 'Small scars matter most when they land in coding or regulatory boundaries.', 'If the junction explanation is shaky, the construct explanation is shaky.'],
         'changing the overlap length or insert orientation'),
    case('Z', 'Multi-Trace Consensus for Final Construct Call', 'D', ['EGFP_CDS'], 'Trace', 'Combine multiple Sanger reads into a consensus, variant table, and final construct verdict.', ['/api/import-ab1', '/api/sanger-consensus', '/api/trace-chromatogram-svg'],
         'When several sequencing reads exist for the same construct, how do you combine them into one decision rather than trusting the loudest trace?',
         'This case uses a real reporter CDS because plasmid verification is one of the most common reasons a lab reaches for sequence traces. The record is familiar, which keeps the attention on evidence integration rather than reference confusion.',
         'Consensus building is an evidence aggregation problem. A single noisy trace can be misleading; several reads can support a stable call, expose mixed positions, and separate expected engineered variants from unexpected errors. The skill is deciding when disagreement reflects noise, chemistry, or a real sequence change.',
         'Consensus is not democracy; three low-quality reads do not magically beat one high-quality read. Quality still matters.',
         {'trace_count': 3, 'expected_variant_positions': [67], 'unexpected_variant_count': 0, 'mixed_position_count': 1, 'final_verdict': 'construct confirmed with expected reporter variant'},
         ['A multi-read consensus report with called-base coverage, variants, and disagreements.', 'A genotype-style check showing whether expected edited positions match the design.', 'A final verification verdict that distinguishes expected variants from unexpected sequence problems.'],
         ['Agreement across independent reads raises confidence, especially when decision-critical positions are supported more than once.', 'Mixed positions are not automatically failures; they are flags that need trace-quality context.', 'Your final call should say whether unexpected variants remain after accounting for the expected design edit.'],
         'changing the read subset, expected variant list, or quality threshold',
         starter_values=[
             'Reference sequence: <code>EGFP_CDS</code>',
             'Read panel: two reads with the expected position-67 training variant plus one parent-like read',
             'Expected bases JSON: <code>{"67":"C"}</code> if the engineered base is C in the training variant',
         ]),
    case('H', 'MSA, Identity Heatmap, and Phylogeny', 'E', ['EGFP_CDS', 'EGFP_Y67H_training_variant', 'EGFP_S204Y_training_variant', 'mCherry_CDS'], 'Advanced', 'Compare a small reporter family panel to see what is conserved, what is engineered, and what is genuinely distant.', ['/api/msa', '/api/heatmap', '/api/phylo'],
         'How do related engineered proteins cluster, and what does that clustering tell you about reuse versus redesign?',
         'This panel mixes two very close EGFP-derived variants with a more distant real reporter, mCherry. That is a good training set because it contains both “small edit” and “different family” comparisons in the same workflow.',
         'The biological point of alignment is not just similarity. It is to identify which regions are constrained, which changes are local engineering edits, and which sequences are far enough apart that transfer of assumptions becomes risky.',
         'A tree is never the biology by itself; it is a summary of the comparison model you chose. But it is still a powerful way to show that one-codon EGFP variants belong in a different interpretive bucket from mCherry.',
         {'panel_size': 4, 'closest_pair': ['EGFP_CDS', 'EGFP_Y67H_training_variant'], 'outgroup_like_member': 'mCherry_CDS', 'interpretation': 'EGFP derivatives cluster tightly, mCherry stays distant'},
         ['A multiple alignment that highlights both conserved backbone and engineered differences.', 'An identity matrix or heatmap showing tight clustering of EGFP-derived variants.', 'A tree or clustering summary that separates close derivatives from distant reporters.'],
         ['Use close clustering to justify localized interpretation, not blanket equivalence.', 'A distant branch is a warning not to overtransfer assumptions from one protein family to another.', 'The most useful comparison is often the one that changes a design decision, not the one that merely looks pretty.'],
         'changing the sequence panel'),
    case('N', 'GC Landscape and Repeat Fragility', 'E', ['mCherry_CDS', 'lacZ_alpha_fragment'], 'Advanced', 'Use analytics tracks to identify composition features that may complicate PCR, synthesis, or sequencing.', ['/api/sequence-analytics'],
         'Where are the composition hotspots that make a seemingly simple sequence harder to amplify or synthesize?',
         'mCherry and the lacZ alpha fragment are both real lab sequences, but they stress workflows differently. Looking at their GC and local complexity profiles teaches you how composition becomes an operational risk even before you do any wet-lab work.',
         'High or uneven GC content, repetitive patches, and abrupt composition transitions can affect polymerase behavior, read quality, and synthesis reliability. This is one of those cases where “nothing is wrong” is still useful information if you can justify it.',
         'A flat, boring composition profile is often good news. In bioinformatics, sometimes the interesting result is that nothing scary shows up.',
         {'highest_gc_window_pct': 68.4, 'repeat_alerts': 1, 'recommended_safe_anchor_region': 'mid-CDS segment with moderate GC'},
         ['An analytics plot or table showing GC and complexity variation along the sequence.', 'At least one region flagged as safer or riskier for assay placement.', 'A note explaining why composition risk does or does not matter for the intended workflow.'],
         ['Composition risk is contextual: a mild hotspot may be irrelevant for cloning but important for PCR primer placement.', 'Use analytics to avoid fragile regions proactively rather than explaining failures afterward.', 'A sequence can be biologically valid and still technically awkward.'],
         'changing the analytics window size'),
    case('O', 'Homopolymer and Low-Complexity Risk Detection', 'E', ['lacZ_alpha_fragment', 'BRAF_exon15_fragment'], 'Search', 'Flag simple-sequence patches that often produce weak confidence in sequencing or synthesis workflows.', ['/api/search-entities', '/api/sequence-analytics'],
         'Do any parts of the sequence look too repetitive or too simple to trust without extra care?',
         'The point here is not that the training sequences are pathological, but that real records often contain local regions that are mechanically harder to read than the rest. Low complexity is a property of the input, not a moral failing of the sample.',
         'Homopolymers and low-complexity patches reduce effective information density. That matters because many experimental and computational methods implicitly assume that neighboring bases provide enough diversity to anchor a confident read or alignment.',
         'The more repetitive a local sequence is, the less each additional base tells you. Information theory shows up in wet-lab troubleshooting more often than people expect.',
         {'low_complexity_windows': 2, 'homopolymer_max_len': 4, 'risk_call': 'moderate caution near simple-sequence patches'},
         ['A list of low-complexity or homopolymer regions with coordinates.', 'A practical judgment about whether those regions threaten the specific workflow.', 'A note about whether extra coverage, alternate primers, or alternate chemistry would help.'],
         ['Simple sequence is not automatically unusable; it just deserves less naive confidence.', 'If a variant call sits in a low-complexity window, ask for another line of evidence.', 'Always tie the risk back to the experiment you actually plan to do.'],
         'changing the complexity threshold'),
    case('X', 'Motif Enrichment and Significance Framing', 'E', ['pUC19_MCS', 'EGFP_CDS', 'mCherry_CDS'], 'Search', 'Compare motif density across engineered vector DNA and reporter CDS records to learn when motif count is meaningful.', ['/api/motif', '/api/search-entities'],
         'When does a motif count reflect biology, and when does it simply reflect that one sequence was engineered to be motif-dense?',
         'The pUC19 multiple-cloning site is intentionally saturated with functional motifs. Reporter CDS records are not. Putting them side by side is a great way to teach why raw motif counts need context.',
         'Motif enrichment can be biologically informative, but it is easy to overclaim. Engineered DNA often has an intentionally non-natural motif distribution. The correct interpretation is therefore comparative: why is one sequence motif-rich, and does that match its design purpose?',
         'A multiple-cloning site is almost a parody of motif enrichment: it was literally designed so many motifs would coexist in one tiny interval.',
         {'pUC19_motif_hits': 6, 'EGFP_motif_hits': 1, 'mCherry_motif_hits': 0, 'interpretation': 'vector motif density is engineered, not mysterious'},
         ['A motif count table or hit map across at least two contrasting records.', 'A contextual explanation for why one sequence has many more motifs than another.', 'A warning against treating count alone as biological significance.'],
         ['Counts become meaningful when compared against sequence purpose, not in isolation.', 'If an engineered vector is motif-rich, that is usually the design, not a surprise.', 'Use motif work to sharpen hypotheses, not to manufacture them.'],
         'changing the queried motif set'),
    case('K', 'CRISPR Candidate and HDR Donor Design', 'F', ['BRAF_exon15_fragment'], 'Advanced', 'Design guide RNAs and an HDR donor around a medically meaningful BRAF hotspot region.', ['/api/grna-design', '/api/crispr-offtargets', '/api/hdr-template'],
         'Can you move from a disease-relevant genomic fragment to a plausible editing plan without pretending that design scores are guarantees?',
         'BRAF exon 15 is a great training target because the biology is genuinely important: this region is a famous hotspot in oncology. Even in a tutorial setting, the design question feels real because the target is real.',
         'CRISPR design is a constraint-balancing problem. You want a guide near the edit, a PAM that works, manageable off-target burden, and a donor that restores the intended sequence cleanly. The biology matters because the wrong edit is not just a technical miss; it changes signaling logic.',
         'Hotspot editing tutorials are memorable because the “why” is obvious: one codon in a kinase can alter growth signaling strongly enough to matter in human disease.',
         {'guide_candidates': 6, 'top_candidate_pam': 'NGG', 'hdr_arms_bp': [60, 60], 'design_goal': 'precise hotspot-local donor template'},
         ['A shortlist of gRNA candidates near the intended edit window.', 'A donor-template design with clearly defined edit and homology arms.', 'An explicit note about off-target risk or why a candidate should be downgraded.'],
         ['A guide closer to the edit is not automatically the best if the off-target profile is ugly.', 'HDR design should be explained in genomic terms: where is the intended edit, and what sequence context supports repair?', 'Treat design scores as prioritization tools, not promises.'],
         'changing the PAM or HDR arm length'),
    case('R', 'Reference-Guided Annotation Transfer', 'B', ['pUC19_MCS', 'EGFP_CDS'], 'Advanced', 'Transfer known EGFP reference annotations onto a candidate vector-plus-reporter construct by similarity.', ['/api/annotation-transfer', '/api/sequence-tracks'],
         'When a new construct contains a familiar part, can you recover the useful feature labels without manually re-annotating every coordinate?',
         'This case combines a pUC19-style cloning context with a real EGFP reporter CDS. The candidate molecule is not just one clean gene; it is a vector context plus an inserted reporter part, which is exactly the situation where reference-guided annotation saves time and reduces coordinate mistakes.',
         'Annotation transfer turns prior knowledge into current context. A reference feature is not blindly copied; it is mapped through sequence similarity and only trusted when identity and feature coverage are high enough. The biological value is that downstream map, track, primer, and validation views inherit the correct functional labels.',
         'Good annotation transfer feels quiet when it works: a familiar part appears in a new construct, and the feature labels land where a scientist expects them.',
         {'source_reference': 'EGFP_CDS_reference', 'target_construct': 'pUC19_MCS + EGFP_CDS', 'transferred_features': ['EGFP reporter CDS', 'gfp N-terminus'], 'identity_pct': 100.0, 'feature_coverage_pct': 100.0},
         ['A transfer report listing source record, identity, feature coverage, and target coordinates.', 'A candidate construct whose feature list now includes the transferred EGFP labels.', 'A follow-up map or sequence track showing that transferred coordinates align with the reporter insert.'],
         ['Similarity-supported transfer is stronger than manual copy-paste because it preserves evidence about identity and coverage.', 'Low coverage should block or downgrade a transferred feature even when part of the sequence looks familiar.', 'Transferred annotations are hypotheses until the target construct and source reference are both trustworthy.'],
         'changing the identity threshold, feature-coverage threshold, or reference record list',
         starter_values=[
             'Target content: <code>pUC19_MCS + EGFP_CDS</code>',
             'Reference record: <code>EGFP_CDS</code> with CDS and gene features',
             'Suggested thresholds: <code>98%</code> identity and <code>95%</code> feature coverage',
         ]),
    case('V', 'Codon Usage Bias and Host Portability', 'F', ['EGFP_CDS', 'mCherry_CDS'], 'Advanced', 'Discuss how two common reporter CDS records might look to different host translation systems.', ['/api/codon-optimize'],
         'If you move a gene between hosts, what sequence properties might become limiting even when the protein target stays the same?',
         'Reporter genes are excellent portability examples because labs routinely move them among bacteria, mammalian cells, and synthetic constructs. The DNA sequence is portable, but the translation machinery and expression context are not identical across hosts.',
         'Codon bias is a reminder that biology has multiple layers of compatibility. The amino-acid sequence may be the same after translation, yet the nucleotide-level implementation can influence expression efficiency, stability, and synthesis convenience in a particular host.',
         'Codon optimization is like changing the accent of a sentence without changing its literal meaning: the content stays similar, but the local audience may understand it far more easily.',
         {'host_comparison': ['E. coli-like', 'mammalian-like'], 'optimization_goal': 'retain protein while changing codon preferences', 'interpretation': 'sequence portability is host-dependent'},
         ['A codon-optimization or codon-bias summary tied to a specific host scenario.', 'A statement about what changed at the nucleotide level and what stayed constant at the protein level.', 'A caution that codon optimization does not solve every expression problem.'],
         ['Codon changes can improve expression without changing the amino-acid sequence, but they can also affect RNA behavior and other features.', 'A portable tutorial answer distinguishes protein identity from nucleotide implementation.', 'Optimization should be justified by a host-specific problem, not used as a reflex.'],
         'changing the target host preference'),
    case('AQ', 'Silent Restriction-Site Engineering', 'F', ['EGFP_CDS'], 'Advanced', 'Search for synonymous coding-sequence edits that introduce or remove a restriction site without changing the translated protein.', ['/api/silent-restriction-sites'],
         'Can you add a convenient screening site to a coding sequence while leaving the protein product unchanged?',
         'This lesson uses EGFP because the coding frame is known and the biological output is easy to understand: if the amino-acid sequence changes unexpectedly, the reporter may stop behaving like EGFP. Silent-site engineering therefore asks for a very specific kind of edit: DNA changes that preserve the protein while adding useful restriction logic.',
         'The key biological concept is degeneracy of the genetic code. Several codons can encode the same amino acid, so not every DNA change changes the protein. That creates a design space where you can install a diagnostic restriction site, remove an unwanted site, or mark a construct version while keeping the amino-acid sequence stable.',
         'The genetic code is redundant in a useful way: biology uses that redundancy naturally, and engineers can sometimes borrow it for construct tracking.',
         {'record': 'EGFP_CDS', 'target_enzyme': 'BamHI', 'frame': 1, 'candidate_type': 'synonymous codon edits', 'protein_preserved': True, 'use_case': 'screening mark or diagnostic digest handle'},
         ['A candidate list of synonymous edits grouped by enzyme and coordinate.', 'For each candidate, a before/after codon comparison that preserves the amino acid.', 'A recommendation about whether the new site is useful enough and safe enough to include.'],
         ['Silent means protein-preserving, not biologically irrelevant; codon usage, RNA structure, or regulatory motifs can still matter.', 'A silent restriction site is most useful when it creates a simple downstream verification assay.', 'Always verify the edited coding sequence in translation context before treating the design as safe.'],
         'changing the enzyme list, frame, or candidate limit',
         starter_values=[
             'Target enzymes: <code>BamHI,EcoRI,HindIII</code>',
             'Frame: <code>1</code>',
             'Candidate limit: <code>20</code>',
         ]),
    case('I', 'DNA Container Roundtrip Validation', 'G', ['EGFP_CDS', 'mCherry_CDS', 'pUC19_MCS'], 'Advanced', 'Export and re-import multiple records to verify that file conversion preserves sequence identity and annotations.', ['/api/export-dna', '/api/import-dna', '/api/canonicalize-record'],
         'Can you move records through a file format boundary without silently changing what the molecule means?',
         'The records in this case are deliberately different: two CDS examples and one compact engineered vector fragment. That makes the roundtrip test more realistic than validating only one simple input type.',
         'Interoperability is a bioinformatics quality problem. A conversion workflow that preserves letters but drops topology, features, or provenance can still damage the scientific value of the record. Roundtrip tests are how you catch that early.',
         'Format conversion bugs are the bioinformatics version of data serialization bugs: the molecule may survive, but the meaning can get stripped away.',
         {'records_tested': 3, 'roundtrip_identity_pct': 100.0, 'annotation_preserved': True, 'status': 'conversion safe for tested bundle'},
         ['A before/after comparison showing that sequence identity survived the roundtrip.', 'A note on whether annotations and topology also survived.', 'A decision about whether the format is safe enough for collaboration or archiving.'],
         ['Sequence identity alone is not enough for full interoperability.', 'A good roundtrip result preserves both content and context.', 'Use canonicalization to make hidden metadata drift visible.'],
         'changing the export target format'),
    case('J', 'AB1 Trace Alignment and Consensus Editing', 'G', ['EGFP_CDS'], 'Trace', 'Import a Sanger-style trace, align it to EGFP, perform an edit, and recompute consensus.', ['/api/import-ab1', '/api/trace-align', '/api/trace-edit', '/api/trace-consensus'],
         'How do raw sequencing traces become a confident construct call instead of just a noisy chromatogram picture?',
         'EGFP is a friendly reference because the expected sequence is familiar, so you can focus on trace logic rather than gene discovery. This case teaches that base calls are inferred from analog signal, not directly observed.',
         'Sanger analysis is where measurement theory becomes concrete. Peaks vary in height and spacing, mixed signal exists, and local noise can create false confidence if you look only at the called letters. Alignment plus manual review is therefore part of the science, not busywork.',
         'A chromatogram is effectively a time-series signal that has been translated into a symbolic sequence. That makes it a very computer-science-friendly piece of biology once you know what you are looking at.',
         {'trace_id_created': True, 'alignment_identity_pct': 99.2, 'edited_base_count': 1, 'consensus_length_bp': 720},
         ['A trace import with a visible chromatogram or summary.', 'An alignment or consensus result that can be compared to the reference sequence.', 'A note explaining whether any manual edit was signal-justified.'],
         ['If the called sequence and the raw peaks disagree, trust the evidence review over the first-pass label.', 'Manual edits should always be justified by the chromatogram, not by wishful thinking about the expected sequence.', 'Consensus calls are stronger when they explain how ambiguity was resolved.'],
         'changing the edited base or alignment window'),
    case('Y', 'Read Simulation and Coverage Planning', 'G', ['BRAF_exon15_fragment', 'EGFP_CDS'], 'Advanced', 'Use realistic target regions to think about how much sequencing evidence is enough for a confident call.', ['/api/trace-consensus', '/api/sequence-analytics'],
         'How much evidence is enough before you should trust a genotype or construct-verification conclusion?',
         'This case contrasts a straightforward reporter CDS with a clinically loaded hotspot fragment. It teaches that “enough coverage” depends on what kind of decision you are making and how fragile the region is.',
         'Coverage planning is about uncertainty management. More reads generally help, but redundancy is not magic if all the reads fail in the same problematic region. The important habit is to ask what failure mode remains possible after the evidence you collected.',
         'One extra read over a hotspot can be worth more than many reads over already-boring sequence.',
         {'target_regions': ['EGFP coding region', 'BRAF hotspot window'], 'recommended_trace_count': {'EGFP_construct_check': 2, 'BRAF_hotspot_call': 3}, 'confidence_rule': 'seek redundant support for decision-critical positions'},
         ['A coverage or evidence plan tied to a real biological question.', 'An explicit explanation of which positions deserve redundant support.', 'A note distinguishing high-confidence and residual-risk regions.'],
         ['Coverage is only meaningful relative to the decision you need to make.', 'Redundant evidence is most valuable at biologically important or technically fragile sites.', 'Always ask what could still go wrong even if the average coverage looks fine.'],
         'changing the hotspot window or number of planned reads'),
    case('AE', 'Sequence Analytics Lens (GC, Skew, Complexity, Stop Density)', 'G', ['EGFP_CDS', 'BRAF_exon15_fragment'], 'Advanced', 'Use the analytics lens on a clean CDS and a genomic fragment to see how sequence context changes interpretation.', ['/api/sequence-analytics'],
         'What do multi-track analytics reveal that plain FASTA text hides?',
         'Putting EGFP next to a genomic BRAF fragment makes the analytics lens more interesting. One record is a polished coding sequence used in expression constructs; the other is a hotspot-rich genomic fragment where translation assumptions are risky.',
         'Analytics tracks help you localize the parts of a molecule that deserve special caution. GC swings, skew changes, low complexity, and stop density are not conclusions by themselves, but they tell you where your attention should go next.',
         'A stop-density track is a very fast way to remind yourself that not every piece of DNA wants to be translated as-is.',
         {'tracks_rendered': ['GC', 'skew', 'complexity', 'stop_density'], 'notable_region': 'BRAF fragment shows coding-context ambiguity', 'safe_region_example': 'mid-EGFP CDS remains compositionally stable'},
         ['A multi-track visualization with at least one biologically interpretable hotspot.', 'A comparison showing why different input classes produce different analytics signatures.', 'A short note about how the analytics view changes your next step.'],
         ['Use analytics as a triage map: where should you zoom in next?', 'A stable profile supports simpler interpretation; a jagged or contradictory one should slow you down.', 'The right conclusion is often “this region needs a different type of evidence.”'],
         'changing the analytics track set or zoom window'),
    case('AF', 'Comparison Lens (Divergence + Confidence Hotspots)', 'G', ['EGFP_CDS', 'EGFP_Y67H_training_variant'], 'Advanced', 'Visualize where two nearly identical sequences diverge and decide whether the divergence matters.', ['/api/comparison-lens'],
         'How do you present a tiny but biologically meaningful difference in a way that a reviewer can understand at a glance?',
         'A near-identical EGFP pair is ideal for the comparison lens because the single engineered difference becomes obvious. That is exactly the kind of case where a text diff is correct but visually underpowered.',
         'The comparison lens is about audience cognition. Human reviewers are bad at scanning long sequences for one consequential difference. A hotspot-focused visualization compresses the reasoning into something reviewable and memorable.',
         'A good comparison plot does not just say “these sequences differ.” It says “they differ here, and that location is the whole story.”',
         {'divergence_hotspots': 1, 'primary_hotspot_bp': '199..201', 'confidence_focus': 'chromophore-adjacent codon'},
         ['A divergence view that localizes where the two records differ.', 'A short statement connecting the hotspot to a functional hypothesis.', 'A reviewer-friendly artifact that can be pasted into notes or reports.'],
         ['If all divergence is concentrated in one short interval, the biology probably is too.', 'Visualization is part of explanation; make the important difference hard to miss.', 'Use hotspot views to support review and handoff, not just personal understanding.'],
         'changing the comparison pair'),
    case('AG', 'Native .dna Import and Multi-Format Conversion Workflow', 'G', ['EGFP_CDS', 'pUC19_MCS'], 'Advanced', 'Demonstrate that a real record can move through multiple formats and come back interpretable.', ['/api/import-dna', '/api/convert', '/api/canonicalize-record'],
         'Can one molecule remain understandable when it is exported into several popular sequence formats?',
         'This case pairs a CDS with a vector fragment because the stress test should include both a gene-like record and an engineered DNA element. That makes the conversion lesson broader than a single happy-path FASTA export.',
         'Format conversion is a scientific communication problem. Different tools and labs prefer different containers, but the underlying biological object should remain stable. The practical skill is checking that nothing biologically important was lost in translation.',
         'The most dangerous format bugs are not obvious corruption. They are subtle meaning loss, such as dropped topology or annotations.',
         {'formats_checked': ['canonical', 'fasta', 'genbank', 'embl', 'json'], 'sequence_identity_pct': 100.0, 'interpretation': 'conversion safe when verified explicitly'},
         ['A multi-format export/import chain using the same underlying record.', 'An explicit before/after comparison of sequence identity and key metadata.', 'A conclusion about which formats are safe enough for your team workflow.'],
         ['Never assume a successful import preserved all the meaning you care about.', 'Prefer workflows that make metadata loss visible rather than silent.', 'The right interoperability habit is verification, not trust.'],
         'changing the export format set'),
    case('AH', 'Chromatogram-First Sanger Review and Confidence Gating', 'G', ['EGFP_CDS'], 'Trace', 'Start with the chromatogram itself before trusting the base calls.', ['/api/import-ab1', '/api/trace-chromatogram-svg'],
         'What does it look like when you review the measurement first and the called letters second?',
         'The input is a familiar reporter reference, which keeps the review cognitively light. The tutorial emphasis is on the chromatogram as raw evidence: peak spacing, peak height, and local ambiguity all matter.',
         'Confidence gating is a mature bioinformatics habit. Instead of assuming every called base is equally trustworthy, you visually separate strong peak regions from weak ones and decide where further evidence is needed.',
         'The chromatogram is a reminder that DNA sequencing is an inference pipeline from analog chemistry to digital symbols.',
         {'high_confidence_window_bp': '40..210', 'low_confidence_window_bp': '5..18', 'review_rule': 'manual review before accepting edge calls'},
         ['A chromatogram view with at least one strong and one weak region called out.', 'A statement explaining which positions are trustworthy enough for automated calls.', 'A note about where manual inspection or extra evidence is required.'],
         ['Strong isolated peaks support confident calls; crowded or flat regions do not.', 'Do not let a polished text export erase your awareness of the underlying signal quality.', 'The most honest answer can be “we need another read here.”'],
         'changing the displayed window or zoom'),
    case('AI', 'Trace-Based Genotyping and Plasmid Verification', 'G', ['BRAF_exon15_fragment', 'EGFP_CDS'], 'Trace', 'Use trace evidence to make either a hotspot genotype call or a plasmid verification call.', ['/api/trace-verify'],
         'How do you turn trace evidence into a yes/no biological decision without pretending the trace is infallible?',
         'Using both a disease-linked fragment and a reporter construct in the same conceptual case shows that the verification logic is shared even when the stakes differ. You are still asking whether the observed sequence agrees with the expected state strongly enough to act.',
         'Verification is an argument from evidence. The trace either supports the expected state, contradicts it, or remains ambiguous. The right scientific move is to make that uncertainty explicit rather than forcing a binary answer too early.',
         'Plasmid verification and genotyping feel like different tasks, but computationally they are cousins: both compare expected and observed sequence states at decision-critical positions.',
         {'verification_mode_examples': ['EGFP plasmid check', 'BRAF hotspot genotype'], 'mismatch_count': 0, 'final_call': 'verified / wild-type-like'},
         ['A verification report localizing any mismatches or confirming identity.', 'A decision-ready verdict that says whether the sample matches expectation.', 'Confidence language explaining whether the result is definitive or provisional.'],
         ['A zero-mismatch result is powerful only if the trace quality is also acceptable.', 'A single mismatch at a critical site can be more important than several low-quality mismatches at unimportant edges.', 'Separate biological consequence from signal confidence in your write-up.'],
         'changing the verification target record'),
    case('AR', 'Linked Trace-to-Reference Navigation', 'G', ['EGFP_CDS'], 'Trace', 'Generate clickable trace/reference navigation anchors so each mismatch or low-confidence call can be inspected in sequence context.', ['/api/import-ab1', '/api/trace-alignment-links', '/api/trace-chromatogram-svg'],
         'When a sequencing trace disagrees with the expected construct, how do you jump directly from the mismatch summary to the raw local evidence?',
         'This lesson again uses EGFP as a familiar reference, but the emphasis is navigation rather than alignment scoring. A trace mismatch is only actionable if you can inspect the surrounding peaks and reference context quickly enough to decide whether the disagreement is real.',
         'Linked navigation turns trace review into an evidence workflow instead of a scavenger hunt. The software localizes each candidate issue, then lets you move between the trace position, reference coordinate, and chromatogram window. Biologically, that matters because a true mutation and a poor base call can look identical in a flat mismatch table until you examine the raw local signal.',
         'A mismatch table without trace navigation is like a stack trace without file links: technically informative, but slower and easier to misread.',
         {'trace_record': 'synthetic EGFP trace', 'reference': 'EGFP_CDS', 'navigation_links': 'one row per aligned base or mismatch focus', 'review_goal': 'inspect raw evidence before accepting or rejecting a variant call'},
         ['A trace import followed by a linked alignment-navigation table.', 'Navigation rows that expose trace position, reference position, local context, and mismatch status.', 'A chromatogram window centered on the position that needs manual review.'],
         ['Linked trace navigation is strongest when you use it to challenge, not merely confirm, the automatic call.', 'A mismatch supported by clean peaks is more biologically meaningful than a mismatch buried in weak signal.', 'The final interpretation should cite both the sequence-level mismatch and the trace-level evidence quality.'],
         'changing the reference sequence or flank size',
         starter_values=[
             'Reference: <code>EGFP_CDS</code>',
             'Flank size: <code>24</code>',
             'Review mode: inspect mismatch and low-quality rows first.',
         ]),
    case('AJ', 'BLAST-like Similarity Search for Identity, Origin, and Contamination', 'G', ['EGFP_CDS', 'mCherry_CDS', 'lacZ_alpha_fragment', 'BRAF_exon15_fragment'], 'Advanced', 'Run local similarity search against a small real-world panel to identify the most likely source of an unknown sequence.', ['/api/blast-search'],
         'If someone hands you a mystery sequence, which known molecule in your local panel does it most resemble?',
         'The training panel mixes reporter genes, a vector-linked fragment, and a human genomic fragment. That is exactly the kind of mixed local reference set a real lab accumulates over time, which makes the search results practically useful.',
         'Similarity search is not just about identity percentages. Coverage, ranking, and context all matter. A high-identity partial hit can mean something very different from a full-length match, especially when you are trying to infer sample origin or contamination.',
         'BLAST-like search is one of the fastest ways to turn a mystery sequence into a shortlist of plausible stories.',
         {'top_hit': 'EGFP_CDS', 'identity_pct': 100.0, 'query_coverage_pct': 100.0, 'runner_up': 'mCherry_CDS'},
         ['A ranked hit list with identity and coverage, not just a single best match.', 'A narrative about what the top hit implies for sample identity or origin.', 'A note explaining whether the hit pattern suggests clean identity or mixed origin.'],
         ['Full-length high-identity hits support strong identity claims.', 'Partial hits are clues, not final answers; always inspect coverage.', 'The runner-up hits often help explain contamination or domain sharing.'],
         'changing the query sequence or database panel'),
    case('AS', 'Selected-Sequence External BLAST Launch', 'G', ['EGFP_CDS'], 'Advanced', 'Package a selected sequence window as FASTA and launch or copy it for external NCBI and WormBase BLAST workflows.', ['/api/blast-launch'],
         'When local search says a sequence is interesting, how do you send exactly the selected region to a public reference search without losing coordinates or context?',
         'The case uses the first coding window of EGFP as a selected region. That is deliberate: a short, biologically meaningful query demonstrates why selected-sequence launch matters. You often do not want to BLAST a whole project file; you want the exact region under your cursor, with a FASTA header that preserves where it came from.',
         'External BLAST is a bridge from local hypothesis to public reference context. Genome Forge does not need to replace every public database. Instead, it should make the handoff precise: selected bases become a clean FASTA payload, the provider launch is explicit, and the user can compare local interpretation with broader NCBI or organism-specific resources.',
         'A good BLAST launch is a tiny provenance package: not just sequence letters, but a name and coordinate story that remind you what you searched.',
         {'selected_record': 'EGFP_CDS', 'selection': '1..240', 'providers': ['NCBI BLAST', 'WormBase BLAST/BLAT', 'WormBase ParaSite BLAST'], 'copy_fasta_header': '>EGFP_CDS_1_240', 'interpretation': 'selected query is ready for public-reference follow-up'},
         ['A copyable FASTA payload for the selected region, not the entire record by accident.', 'Provider-specific launch links or instructions for NCBI and WormBase-style BLAST workflows.', 'A note recording which coordinate window was searched so the result remains auditable.'],
         ['External BLAST results should refine local interpretation, not erase local context.', 'The most common user error is searching the wrong region; coordinate-aware FASTA headers reduce that risk.', 'For organism-specific workflows, provider choice matters because database scope changes what a top hit means.'],
         'changing the selected start/end coordinates or provider list',
         starter_values=[
             'Selection: <code>1..240</code>',
             'Providers: <code>ncbi,wormbase,wormbase_parasite</code>',
             'Record name: <code>EGFP_CDS</code>',
         ]),
    case('AT', 'NGS-Lite Amplicon Evidence Report', 'G', ['EGFP_CDS'], 'NGS Lite', 'Run a compact FASTQ QC, trimming, read-mapping, and variant-evidence workflow for an EGFP amplicon.', ['/api/fastq-qc', '/api/fastq-trim', '/api/ngs-map-reads', '/api/ngs-workflow-report'],
         'Can a small amplicon read set confirm the expected reporter edit while also making quality, adapter trimming, and coverage gaps visible?',
         'The example uses the familiar EGFP reporter so the biological object is easy to reason about. The sequencing evidence is intentionally small: a handful of overlapping amplicon reads, one planned variant, and one adapter-contaminated tail. That is enough to teach how FASTQ quality and coverage support or weaken a construct-verification call.',
         'NGS-lite evidence is not about pretending a small local workflow replaces a production secondary-analysis stack. It is about making the core reasoning loop visible: inspect read quality, trim obvious technical artifacts, map reads to the intended reference, check coverage at decision-critical positions, and separate expected variants from surprises.',
         'FASTQ looks like plain text, but every base carries a tiny confidence score; treating those scores as first-class evidence is what makes sequencing feel less magical.',
         {'read_count': 4, 'adapter_hit_count_before_trim': 1, 'adapter_hit_count_after_trim': 0, 'expected_variant': 'EGFP position 67', 'workflow_verdict': 'PASS', 'phase_rows': ['construct verification', 'sequence analysis', 'NGS-lite pipeline', 'trust evidence']},
         ['A FASTQ QC report that detects adapter contamination and summarizes read quality.', 'A trimming audit showing the adapter-bearing tail was removed without dropping useful reads.', 'A mapping and variant report that confirms the expected edit, reports coverage, and flags unexpected variants separately.'],
         ['Coverage at the expected edit is more important than a pretty overall read count.', 'Adapter trimming changes what evidence is available, so the trim audit is part of the scientific record.', 'A PASS verdict is strongest when quality, coverage, expected-variant support, and absence of unexpected variants all point the same way.'],
         'changing minimum depth, alternate fraction, or expected-variant JSON',
         starter_values=[
             'Use the NGS Lite panel default FASTQ reads, then replace the reference with the first <code>180</code> bp of <code>EGFP_CDS</code> for the full exercise.',
             'Expected variants JSON: <code>{"67":"C"}</code> when using the generated EGFP amplicon example.',
             'Adapter: <code>AGATCGGAAGAGC</code>; trim quality: <code>20</code>; minimum length: <code>60</code>.',
         ]),
    case('AK', 'Reference Element Auto-Flagging and siRNA Design/Mapping', 'G', ['EGFP_CDS', 'mCherry_CDS'], 'Advanced', 'Reuse saved element libraries to auto-flag familiar sequence elements, then design and map siRNA candidates.', ['/api/reference-db-save', '/api/reference-scan', '/api/sirna-design', '/api/sirna-map'],
         'How do reusable sequence libraries turn repeated manual annotation into a faster and more consistent design workflow?',
         'Reporter CDS records are excellent for this because many labs annotate the same elements repeatedly. Saving reference libraries means the machine can recognize them quickly, and the same sequence can then be repurposed for knockdown-style thinking via siRNA design.',
         'This case is about reuse. Bioinformatics becomes dramatically more efficient when previously understood sequence elements are captured as searchable reference knowledge rather than rediscovered each time.',
         'The value of a reference library is partly speed, but mostly consistency: the same sequence gets recognized the same way every time.',
         {'reference_hits': ['EGFP CDS', 'mCherry CDS'], 'top_sirna_candidate_count': 5, 'mapped_binding_sites': 5},
         ['A reference-scan result showing which familiar elements were auto-flagged.', 'A ranked siRNA candidate list with mapped target positions.', 'A note explaining why reuse of reference knowledge reduces human error.'],
         ['Auto-flagging is strongest when the reference database is curated and versioned.', 'siRNA ranking is still a prioritization tool; experimental validation remains necessary.', 'The useful lesson is workflow reuse: annotation and design can feed each other.'],
         'changing the reference library or siRNA ranking cutoff'),
    case('AM', 'Ambiguity-Aware Identity Search and Motif Rescue', 'G', ['EGFP_CDS', 'EGFP_ambiguity_consensus_training', 'mCherry_CDS'], 'Advanced', 'Treat an ambiguity-bearing consensus record as a real query and verify that identity search and motif logic still recover the correct biological family.', ['/api/motif', '/api/blast-search', '/api/search-entities'],
         'If a sequence contains unresolved positions, can you still recover its likely identity and use it responsibly instead of discarding it as “bad data”?',
         'The key input here is not a perfect sequence but a partially uncertain one. The ambiguity-bearing EGFP consensus stands in for a realistic intermediate artifact: a query that is clearly close to a known reporter family, yet still carries unresolved positions from sequencing or consensus assembly.',
         'A huge amount of practical bioinformatics is about deciding what to do before the data are perfectly clean. Ambiguity codes let you represent uncertainty honestly. Ambiguity-aware search then lets you ask whether the uncertain record is still informative enough to identify, classify, or troubleshoot. The lesson is not that ambiguity disappears. The lesson is that uncertainty can still be computationally useful when represented explicitly.',
         'The scientific upgrade is subtle but important: you move from “this sequence is messy” to “this sequence still rules out many stories and supports a smaller plausible set.”',
         {'query_record': 'EGFP_ambiguity_consensus_training', 'motif_query': 'ATGGTGRG', 'top_blast_hit': 'EGFP_CDS', 'identity_pct': 100.0, 'query_coverage_pct': 100.0, 'runner_up': 'mCherry_CDS', 'interpretation': 'uncertain positions did not erase reporter-family identity'},
         ['A motif or similarity search in which an ambiguity-containing query still returns a biologically sensible top match.', 'A ranked hit list that shows why the correct family remains the strongest explanation.', 'A short statement separating what is still known confidently from what remains unresolved.'],
         ['Ambiguity-aware search should narrow the plausible identity space even when it cannot force every base to one final call.', 'A strong top hit with high coverage means the uncertain sequence is still informative, not that uncertainty vanished.', 'The right interpretation sounds like “this is still EGFP-family-like, with unresolved positions at specific sites,” not “the data are now magically exact.”'],
         'changing the ambiguous query window or comparison panel',
         starter_values=[
             'Query record: <code>EGFP_ambiguity_consensus_training</code>',
             'Example motif query: <code>ATGGTGRG</code>',
             'Comparison panel: <code>EGFP_CDS, EGFP_ambiguity_consensus_training, mCherry_CDS</code>',
         ]),
    case('L', 'Collaboration, Audit, and Review Governance', 'H', ['EGFP_CDS'], 'Advanced', 'Create a workspace, assign roles, and run a simple review flow on a saved construct project.', ['/api/workspace-create', '/api/project-permissions', '/api/review-submit', '/api/review-approve'],
         'How do you make sequence work reviewable by another person instead of leaving it as personal screen state?',
         'This governance cluster deliberately uses a familiar record so the tutorial attention stays on process rather than molecular interpretation. The point is to show how sequence work becomes team knowledge.',
         'Scientific reproducibility depends on more than file storage. Roles, review, audit trails, and explicit approval states are part of the computational record. Without them, a project may be technically complete but socially fragile.',
         'In modern labs, the “truth” of a construct often lives partly in people and partly in software; governance features are how you keep those from drifting apart.',
         {'workspace_created': True, 'roles': {'owner_user': 'owner', 'editor_user': 'editor', 'reviewer_user': 'reviewer'}, 'review_status': 'approved'},
         ['A saved project with explicit role assignments and a traceable review event.', 'An audit-friendly record of who changed or approved what.', 'A clear explanation of why governance matters for scientific trust.'],
         ['A sequence project that cannot be reviewed cleanly is harder to trust and harder to reuse.', 'Audit logs are most valuable when something becomes confusing later; build them before confusion arrives.', 'Governance features are scientific infrastructure, not bureaucracy for its own sake.'],
         'changing the assigned role or review state'),
    case('T', 'Batch Reproducibility and Parameter Locking', 'H', ['EGFP_CDS', 'mCherry_CDS', 'BRAF_exon15_fragment'], 'Advanced', 'Run the same logic across several records with a locked parameter set so outputs stay comparable.', ['/api/project-save', '/api/sequence-analytics', '/api/batch-digest'],
         'How do you make sure that differences between records reflect biology instead of accidental parameter drift?',
         'Batch work is where reproducibility discipline becomes visible. Using several real records with one locked configuration lets you compare outputs honestly instead of wondering whether the settings changed between runs.',
         'Parameter locking matters because software is part of the experiment. If settings drift invisibly, your comparison is no longer about molecules alone. Reproducibility begins when you can state exactly what was held constant.',
         'A batch run is only comparable if the software treated each input under the same contract.',
         {'record_count': 3, 'parameter_profile': 'locked', 'comparison_ready': True},
         ['A batch run with identical settings applied to multiple records.', 'A written record of the locked parameter profile.', 'A statement about what differences can now be attributed to biology rather than settings.'],
         ['Locked parameters create fair comparisons.', 'If a rerun needs different settings, treat it as a new experiment and say so.', 'Reproducibility is easiest when the configuration is explicit and boring.'],
         'changing one parameter intentionally to test robustness'),
    case('AB', 'Reproducible Report Package', 'H', ['EGFP_CDS', 'pUC19_MCS'], 'Advanced', 'Package a saved project and a share bundle so another scientist can reopen the same analysis context.', ['/api/project-save', '/api/share-create', '/api/share-load'],
         'What does a handoff artifact look like when you want another person to inspect the same biological object, not just hear about it?',
         'This case treats the molecular record as a deliverable. Using a familiar reporter/vector pair keeps the content concrete while shifting the lesson toward packaging and transport of scientific context.',
         'A reproducible report package includes the molecule, the interpretation, and the route back to the evidence. Sharing only screenshots or only FASTA is usually not enough. The useful package is the one another person can actually reopen and interrogate.',
         'A good handoff is a kindness to your future self as much as to your collaborators.',
         {'project_saved': True, 'share_bundle_created': True, 'project_count': 1, 'handoff_ready': True},
         ['A saved project plus a reloadable share bundle.', 'A note describing what context the package preserves.', 'A simple check that another user or browser session can reopen the artifact.'],
         ['A package is only reproducible if it can be reopened independently of your current browser state.', 'Think of share bundles as portable scientific state, not just exported files.', 'The less hidden context a handoff requires, the better the handoff.'],
         'changing whether content is embedded in the bundle'),
    case('AC', 'Parameter Sensitivity and Robustness Check', 'H', ['BRAF_exon15_fragment', 'EGFP_CDS'], 'Advanced', 'Rerun a workflow under a small parameter sweep to see whether the biological conclusion is robust or fragile.', ['/api/primer-design', '/api/grna-design', '/api/sequence-analytics'],
         'Would you reach the same biological conclusion if a reasonable analyst chose slightly different parameters?',
         'This case is built around the uncomfortable but essential idea that a strong pipeline should tolerate small setting changes. Real biological examples help here because the outputs matter more when the records are not invented toys.',
         'Sensitivity analysis is how you keep yourself honest. If a conclusion flips under small parameter nudges, the conclusion is fragile and should be reported as such. Robustness is not a brag; it is a property you test.',
         'Some of the best scientific writing consists of one calm sentence saying, “this result is parameter-sensitive, so treat it cautiously.”',
         {'parameter_sweep_size': 3, 'robust_call_examples': ['EGFP length and ORF remain stable'], 'fragile_call_example': 'borderline primer ranking can flip'},
         ['A mini-sweep with at least one stable output and one potentially fragile output.', 'A note about which conclusions remain trustworthy across settings.', 'A recommendation for how to report or mitigate fragile results.'],
         ['Stable outputs earn confidence; fragile outputs earn caution.', 'A parameter-sensitive result is not useless, but it should be presented with narrower claims.', 'Sensitivity analysis is part of interpretation, not just a software exercise.'],
         'changing one threshold across a small sweep'),
    case('AD', 'End-to-End Release Checklist and Handoff', 'H', ['EGFP_CDS', 'mCherry_CDS', 'pUC19_MCS', 'BRAF_exon15_fragment'], 'Advanced', 'Treat the tutorial workspace like a releasable scientific software product and verify the handoff boundary.', ['/api/project-save', '/api/share-create', '/api/project-history-svg'],
         'If you had to stop work today and let another person continue tomorrow, what would they need?',
         'The final case intentionally zooms out. The real-world molecules are now ingredients in a process story: save state, capture provenance, package outputs, and document what still needs verification. That is what mature scientific computing looks like.',
         'End-to-end handoff is where software engineering and biology meet most directly. A good package includes executable steps, sample data, known limitations, and enough context that a new person can rerun the work without guessing what mattered.',
         'A handoff is successful when the next person says “I know where to start,” not when they say “I have the files.”',
         {'checklist_items': ['sample data bundled', 'tutorial regenerated', 'PDF built', 'tests passed'], 'handoff_state': 'ready'},
         ['A release-style checklist that covers data, docs, state, and verification.', 'A clear statement of what remains uncertain or intentionally simplified.', 'A handoff artifact that helps the next person continue without hidden memory.'],
         ['The final deliverable is not the molecule alone; it is the reproducible workflow around the molecule.', 'The best handoff documents both what works and what is still risky.', 'Zero-memory pickup is a great standard for scientific software because people and projects always get interrupted.'],
         'changing the handoff checklist or packaged artifacts'),
]


CLUSTER_CASES = {
    cluster['id']: [case for case in CASES if case['cluster'] == cluster['id']]
    for cluster in CLUSTERS
}


def load_fasta_records() -> dict[str, str]:
    records: dict[str, str] = {}
    name: str | None = None
    chunks: list[str] = []
    for line in FASTA_PATH.read_text(encoding='utf-8').splitlines():
        if line.startswith('>'):
            if name is not None:
                records[name] = ''.join(chunks)
            name = line[1:].strip()
            chunks = []
        else:
            chunks.append(line.strip())
    if name is not None:
        records[name] = ''.join(chunks)
    return records


def apply_edits(seq: str, edits: list[dict]) -> str:
    new_seq = seq
    offset = 0
    for edit in edits:
        start = int(edit['start_1based']) - 1 + offset
        end = int(edit['end_1based']) + offset
        replacement = str(edit['replacement'])
        new_seq = new_seq[:start] + replacement + new_seq[end:]
        offset += len(replacement) - (end - start)
    return new_seq


def resolved_record_sequence(record_name: str, base_sequences: dict[str, str]) -> str:
    rec = RECORDS[record_name]
    if 'sequence_ref' in rec:
        ref_name = str(rec['sequence_ref']).split(':', 1)[1]
        return base_sequences[ref_name]
    if 'derived_from' in rec:
        return apply_edits(resolved_record_sequence(rec['derived_from'], base_sequences), list(rec.get('edits', [])))
    raise KeyError(record_name)


def format_json_block(payload: dict) -> str:
    return escape(json.dumps(payload, indent=2, sort_keys=False))


def format_list(items: list[str], *, escape_items: bool = True) -> str:
    if escape_items:
        return ''.join(f'<li>{escape(item)}</li>' for item in items)
    return ''.join(f'<li>{item}</li>' for item in items)


def render_nested_list(items: list[str]) -> str:
    return '<ul>' + format_list(items) + '</ul>'


def render_record_badges(records: list[str]) -> str:
    return ''.join(f'<span class="badge">{escape(record)}</span>' for record in records)


def guide_for_case(case_info: dict) -> dict:
    for api in case_info['apis']:
        for guide in UI_GUIDES:
            if guide['match_api'] == api:
                return guide
    return {
        'tab': case_info['tab'],
        'fields': ['Sequence / FASTA / GenBank', 'Name', 'Topology', 'Frame', 'workflow-specific controls'],
        'button': case_info['workflow'],
        'panel': 'Results plus the matching visualization panel',
        'sample': 'Use the starter values below when provided; otherwise run the default setting first.',
        'troubleshoot': 'If your result differs, confirm the loaded record, topology, frame, and window before changing biological interpretation.',
    }


def render_exact_ui_steps(case_info: dict) -> str:
    guide = guide_for_case(case_info)
    fields = ', '.join(f'<code>{escape(field)}</code>' for field in guide['fields'])
    steps = [
        f'Load the included prebuilt bundle <code>{escape(prebuilt_case_bundle_path(case_info["id"]))}</code> into <code>Sequence / FASTA / GenBank</code>. Keep <code>Name</code> descriptive and set <code>Topology</code> according to the bundle manifest.',
        f'Open the <code>{escape(guide["tab"])}</code> tab. Confirm these UI landmarks before running: {fields}.',
        f'{guide["sample"]}',
        f'Click <code>{escape(guide["button"])}</code>. The primary visible result should appear in <code>{escape(guide["panel"])}</code> and the JSON details should appear in <code>Results</code>.',
        f'Compare your output with the sample result below. If it differs, use this first troubleshooting rule: {guide["troubleshoot"]}',
        f'Write one sentence beginning “The evidence supports...” and one sentence beginning “The next bench decision is...”. Keep the endpoint record with <code>{escape(", ".join(case_info["apis"]))}</code>.',
    ]
    return '<div class="stepbox"><b>Step-by-Step in Genome Forge: Exact UI Walkthrough</b><ol>' + format_list(steps, escape_items=False) + '</ol></div>'


def glossary_terms_for_case(case_info: dict) -> list[str]:
    text = ' '.join([
        case_info['title'],
        case_info['workflow'],
        case_info['biological_question'],
        case_info['biology'],
        ' '.join(case_info['apis']),
        ' '.join(case_info['records']),
    ]).lower()
    selected = []
    for term in GLOSSARY_TERMS:
        if term.lower() in text:
            selected.append(term)
    if any(api in case_info['apis'] for api in ['/api/translate', '/api/orfs', '/api/silent-restriction-sites', '/api/codon-optimize']):
        selected.extend(['CDS', 'ORF', 'frame', 'codon'])
    if any(api in case_info['apis'] for api in ['/api/digest', '/api/digest-advanced', '/api/restriction-compare', '/api/silent-restriction-sites']):
        selected.extend(['restriction site', 'methylation'])
    if any(api.startswith('/api/trace') or api in ['/api/import-ab1', '/api/sanger-consensus'] for api in case_info['apis']):
        selected.extend(['Sanger trace', 'consensus'])
    if any(api in case_info['apis'] for api in ['/api/fastq-qc', '/api/fastq-trim', '/api/ngs-map-reads', '/api/ngs-workflow-report']):
        selected.extend(['FASTQ', 'coverage', 'variant', 'consensus'])
    if any(api in case_info['apis'] for api in ['/api/pcr', '/api/pcr-gel-lanes', '/api/primers']):
        selected.append('amplicon')
    deduped = []
    for term in selected:
        if term in GLOSSARY_TERMS and term not in deduped:
            deduped.append(term)
    return deduped[:5]


def render_case_glossary(case_info: dict) -> str:
    terms = glossary_terms_for_case(case_info)
    if not terms:
        terms = ['topology', 'restriction site', 'frame']
    rows = ''.join(
        dedent(f'''
        <div class="glossary-card">
          <h4>{escape(term)}</h4>
          <p><b>Meaning:</b> {escape(GLOSSARY_TERMS[term]['definition'])}</p>
          <p><b>CS analogy:</b> {escape(GLOSSARY_TERMS[term]['cs_analogy'])}</p>
          <p><b>Why it matters:</b> {escape(GLOSSARY_TERMS[term]['why_it_matters'])}</p>
        </div>
        ''').strip()
        for term in terms
    )
    return f'<div class="glossary-strip"><b>Just-in-Time Glossary</b><div class="glossary-grid">{rows}</div></div>'


def decision_profile(case_info: dict) -> dict[str, str]:
    apis = set(case_info['apis'])
    title = case_info['title'].lower()
    if '/api/restriction-compare' in apis or 'diagnostic' in title:
        return {
            'decision': 'Choose the enzyme only if it creates a readable difference between the related molecules.',
            'bench': 'Run a small diagnostic digest and compare the observed gel bands with the predicted parent/variant patterns.',
            'caution': 'Do not prefer a cutter merely because it cuts often; prefer the cutter that answers the discrimination question cleanly.',
        }
    if '/api/silent-restriction-sites' in apis:
        return {
            'decision': 'Proceed only after confirming the edit preserves translation and does not create an unwanted local feature.',
            'bench': 'Order or clone the silent-edit design, then verify with both sequencing and the new digest handle.',
            'caution': 'Silent means amino-acid-preserving, not automatically consequence-free.',
        }
    if any(api.startswith('/api/trace') or api in {'/api/import-ab1', '/api/sanger-consensus'} for api in apis):
        return {
            'decision': 'Accept the construct only where trace peaks support the called sequence at decision-critical bases.',
            'bench': 'Repeat sequencing or add an opposite-strand read if the chromatogram is weak, mixed, or edge-biased.',
            'caution': 'A clean-looking consensus is not stronger than the raw trace evidence behind it.',
        }
    if any(api in apis for api in {'/api/fastq-qc', '/api/fastq-trim', '/api/ngs-map-reads', '/api/ngs-workflow-report'}):
        return {
            'decision': 'Accept the construct only when expected edits have enough high-quality read support and coverage gaps do not touch decision-critical positions.',
            'bench': 'Repeat or deepen the amplicon run if trimming removes too much evidence, coverage is sparse, or unexpected variants survive thresholding.',
            'caution': 'A high-support local variant report is useful construct evidence, but it is not a substitute for production-grade NGS secondary analysis.',
        }
    if '/api/blast-launch' in apis or '/api/blast-search' in apis:
        return {
            'decision': 'Use public-search hits to refine identity hypotheses, not to erase local coordinate context.',
            'bench': 'Follow up surprising hits by checking contamination, query length, coverage, and database scope.',
            'caution': 'Top hit, high identity, and biological identity are related but not identical claims.',
        }
    if any(api in apis for api in ['/api/primers', '/api/pcr', '/api/pcr-gel-lanes', '/api/primer-diagnostics']):
        return {
            'decision': 'Use the primer pair only if specificity, size, Tm, and interpretation all support the assay goal.',
            'bench': 'Run the predicted product with appropriate positive and negative controls.',
            'caution': 'A primer that binds somewhere is not necessarily a primer that produces an interpretable experiment.',
        }
    if any(api in apis for api in ['/api/project-save', '/api/share-create', '/api/review-submit']):
        return {
            'decision': 'Treat the saved project as acceptable only if another person can reopen the data, evidence, and reasoning.',
            'bench': 'Use the handoff package for review, repetition, or continuation by another team member.',
            'caution': 'Screenshots are not reproducibility; saved state plus provenance is closer.',
        }
    return {
        'decision': 'Proceed when the output answers the biological question and the assumptions match the input data type.',
        'bench': 'Translate the software result into the next physical or review action before changing the molecule.',
        'caution': 'Do not report the tool output as the conclusion; report the defensible biological interpretation.',
    }


def render_evidence_inference(case_info: dict) -> str:
    profile = decision_profile(case_info)
    evidence = [
        case_info['expected'][0],
        f"Input records: {', '.join(case_info['records'])}.",
        f"Primary endpoint(s): {', '.join(case_info['apis'])}.",
    ]
    inference = [
        case_info['interpretation'][0],
        profile['decision'],
        profile['caution'],
    ]
    return dedent(f'''
      <div class="evidence-box">
        <b>Evidence vs Inference</b>
        <div class="evidence-grid">
          <div><h4>Observed Evidence</h4>{render_nested_list(evidence)}</div>
          <div><h4>Defensible Inference</h4>{render_nested_list(inference)}</div>
        </div>
      </div>
    ''').strip()


def render_decision_card(case_info: dict) -> str:
    profile = decision_profile(case_info)
    return dedent(f'''
      <div class="decision-card">
        <b>Bench Decision Card</b>
        <p><span>Decision:</span> {escape(profile['decision'])}</p>
        <p><span>Bench consequence:</span> {escape(profile['bench'])}</p>
        <p><span>Confidence limit:</span> {escape(profile['caution'])}</p>
      </div>
    ''').strip()


def common_mistakes(case_info: dict) -> list[tuple[str, str]]:
    apis = set(case_info['apis'])
    if '/api/restriction-compare' in apis:
        return [
            ('Wrong interpretation', 'The enzyme with the most cuts is automatically best.'),
            ('Correction', 'The best diagnostic cutter creates a simple, readable difference between the exact two molecules being compared.'),
        ]
    if '/api/silent-restriction-sites' in apis:
        return [
            ('Wrong interpretation', 'A silent edit cannot matter biologically.'),
            ('Correction', 'It preserves the amino acid, but you still check codon usage, RNA context, and unwanted feature creation.'),
        ]
    if any(api.startswith('/api/trace') or api in {'/api/import-ab1', '/api/sanger-consensus'} for api in apis):
        return [
            ('Wrong interpretation', 'The exported base call is the raw experimental fact.'),
            ('Correction', 'The chromatogram is the rawer evidence; base calls and consensus are interpretations of that signal.'),
        ]
    if any(api in apis for api in {'/api/fastq-qc', '/api/fastq-trim', '/api/ngs-map-reads', '/api/ngs-workflow-report'}):
        return [
            ('Wrong interpretation', 'A variant in the table is automatically a biological truth.'),
            ('Correction', 'Interpret the variant with depth, base quality, expected-edit status, zero-coverage regions, and sample provenance.'),
        ]
    if '/api/blast-launch' in apis or '/api/blast-search' in apis:
        return [
            ('Wrong interpretation', 'The top hit proves identity.'),
            ('Correction', 'Interpret top hits together with query length, coverage, database scope, and local sample context.'),
        ]
    if any(api in apis for api in ['/api/translate', '/api/orfs', '/api/codon-optimize']):
        return [
            ('Wrong interpretation', 'Any long ORF means the biological object is a complete gene.'),
            ('Correction', 'An ORF is a clue; annotation, frame, source, and experimental context decide meaning.'),
        ]
    return [
        ('Wrong interpretation', 'If the software output looks clean, the biological conclusion is settled.'),
        ('Correction', 'A clean output still depends on the input record, parameters, evidence quality, and the decision you are trying to support.'),
    ]


def render_common_mistakes(case_info: dict) -> str:
    rows = ''.join(
        f'<p><span>{escape(label)}:</span> {escape(text)}</p>'
        for label, text in common_mistakes(case_info)
    )
    return f'<div class="mistake-box"><b>Common Wrong Interpretation</b>{rows}</div>'


def render_lab_chief_checklist(case_info: dict) -> str:
    profile = decision_profile(case_info)
    prompts = [
        f"What biological object are we handling: {', '.join(case_info['records'])}?",
        "What would go wrong at the bench if this interpretation is wrong?",
        "Which output is evidence, and which sentence is inference?",
        f"What is the next action: {profile['bench']}",
    ]
    return '<div class="chief-box"><b>Lab-Chief Teaching Prompts</b><ul>' + format_list(prompts) + '</ul></div>'


def render_cluster_checkpoint(cluster: dict) -> str:
    cases = CLUSTER_CASES[cluster['id']]
    first_case = cases[0]
    last_case = cases[-1]
    precheck = [
        f"Before starting, state the biological object type for Case {first_case['id']} without looking at the answer key.",
        "Name one thing the software can measure directly and one thing you must infer biologically.",
        "Predict which UI panel will produce the main evidence for this cluster.",
    ]
    postcheck = [
        f"After finishing Case {last_case['id']}, write the next bench or review action in one sentence.",
        "Identify one parameter that could change confidence without changing the raw sequence.",
        "Explain one common wrong interpretation and how the corrected reasoning avoids it.",
    ]
    roleplay = [
        "Intern: summarize the result in plain English without jargon.",
        "Lab chief: challenge the evidence quality and ask what would fail at the bench.",
        "Program manager: record whether the tutorial, UI, or data bundle caused avoidable friction.",
    ]
    return dedent(f'''
      <div class="cluster-checkpoint">
        <b>Cluster Checkpoint and Role-Play</b>
        <div class="checkpoint-grid">
          <div><h4>Pre-check</h4>{render_nested_list(precheck)}</div>
          <div><h4>Post-check</h4>{render_nested_list(postcheck)}</div>
          <div><h4>Training Role-Play</h4>{render_nested_list(roleplay)}</div>
        </div>
      </div>
    ''').strip()


def render_global_glossary() -> str:
    rows = ''.join(
        '<tr>'
        f'<td><code>{escape(term)}</code></td>'
        f'<td>{escape(info["definition"])}</td>'
        f'<td>{escape(info["cs_analogy"])}</td>'
        f'<td>{escape(info["why_it_matters"])}</td>'
        '</tr>'
        for term, info in sorted(GLOSSARY_TERMS.items(), key=lambda item: item[0].lower())
    )
    return (
        '<table>'
        '<thead><tr><th>Term</th><th>Biology meaning</th><th>CS analogy</th><th>Why it matters in the lab</th></tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table>'
    )


def render_cheat_sheets() -> str:
    cards = ''.join(
        dedent(f'''
        <div class="cheat-card">
          <h3>{escape(sheet['title'])}</h3>
          <p><b>Use when:</b> {escape(sheet['use_when'])}</p>
          <p><b>Read for:</b> {escape(', '.join(sheet['read_for']))}</p>
          <p><b>Common trap:</b> {escape(sheet['common_trap'])}</p>
        </div>
        ''').strip()
        for sheet in CHEAT_SHEETS
    )
    return f'<div class="cheat-grid">{cards}</div>'


def record_reference_table() -> str:
    rows = []
    for name, info in RECORDS.items():
        rows.append(
            '<tr>'
            f'<td><code>{escape(name)}</code><div class="tiny muted">{escape(info["type"])}</div></td>'
            f'<td>{escape(info["origin"])}</td>'
            f'<td>{escape(info["why_it_matters"])}</td>'
            f'<td>{escape(info["input_details"])}</td>'
            f'<td><a href="{escape(info["source_url"])}">{escape(info["source_label"])}</a></td>'
            '</tr>'
        )
    return ''.join(rows)


def case_bundle_command(case_id: str) -> str:
    return f'python3 docs/tutorial/datasets/extract_case_bundle.py --case {case_id} --out ./tmp/genomeforge_case_{case_id.lower()}'


def prebuilt_case_bundle_path(case_id: str) -> str:
    return f'docs/tutorial/datasets/case_bundles/case_{case_id.lower()}/records.fasta'


def _count_site(seq: str, motif: str) -> int:
    total = 0
    start = 0
    while True:
        idx = seq.find(motif, start)
        if idx == -1:
            return total
        total += 1
        start = idx + 1


def _frame_stop_count(seq: str, frame: int = 1) -> int:
    stops = {'TAA', 'TAG', 'TGA'}
    offset = max(0, int(frame) - 1)
    return sum(1 for i in range(offset, len(seq) - 2, 3) if seq[i:i + 3] in stops)


def _pairwise_identity(seq_a: str, seq_b: str) -> float:
    if len(seq_a) != len(seq_b):
        raise ValueError('Sequences must have equal length for simple identity')
    mismatches = sum(1 for left, right in zip(seq_a, seq_b) if left != right)
    return round((len(seq_a) - mismatches) / max(1, len(seq_a)) * 100.0, 3)


def compute_featured_results() -> list[dict[str, str]]:
    base_sequences = load_fasta_records()
    egfp = resolved_record_sequence('EGFP_CDS', base_sequences)
    mcherry = resolved_record_sequence('mCherry_CDS', base_sequences)
    puc = resolved_record_sequence('pUC19_MCS', base_sequences)
    braf = resolved_record_sequence('BRAF_exon15_fragment', base_sequences)
    y67h = resolved_record_sequence('EGFP_Y67H_training_variant', base_sequences)
    ambiguous = resolved_record_sequence('EGFP_ambiguity_consensus_training', base_sequences)
    common_sites = ['GAATTC', 'GGATCC', 'AAGCTT', 'TCTAGA', 'CTGCAG', 'GGTACC']
    unique_sites = sum(1 for motif in common_sites if _count_site(puc, motif) == 1)
    return [
        {
            'title': 'EGFP is a clean coding-sequence teaching record',
            'value': f'{len(egfp)} bp → {(len(egfp) - 3) // 3} aa + stop',
            'story': 'That makes it ideal for learning frame-aware translation, variant annotation, and plasmid verification without the extra ambiguity of introns or splice context.',
        },
        {
            'title': 'The pUC19 multiple-cloning site is densely engineered',
            'value': f'{len(puc)} bp with {unique_sites} common unique sites',
            'story': 'This tiny region packs a surprising amount of experimental flexibility into a few dozen bases, which is why it became a cloning-era classic.',
        },
        {
            'title': 'Restriction comparison turns small edits into screenable assays',
            'value': 'Parent-versus-variant cutter logic now has its own lesson path',
            'story': 'The tutorial now teaches how to find enzymes that cut one related construct but not the other, then connect that computational difference to a practical diagnostic digest.',
        },
        {
            'title': 'A one-codon EGFP derivative can still be biologically dramatic',
            'value': f'EGFP vs Y67H-like variant: {_pairwise_identity(egfp, y67h)}% nucleotide identity',
            'story': 'The tutorial uses this to teach a core lesson in molecular biology: a small sequence delta can carry a large phenotype when it lands in a privileged site.',
        },
        {
            'title': 'The BRAF training fragment is genomic context, not a standalone CDS',
            'value': f'{len(braf)} bp with {_frame_stop_count(braf)} naive frame-1 stop codons',
            'story': 'That is exactly what makes it useful. It forces you to distinguish “this DNA is wrong” from “this DNA is a different biological object than a clean coding sequence.”',
        },
        {
            'title': 'Reporter proteins can do similar jobs while having different sequence histories',
            'value': f'EGFP length {len(egfp)} bp vs mCherry length {len(mcherry)} bp',
            'story': 'Comparing them is a good reminder that “same use in the lab” does not imply “same sequence architecture” or even the same engineering tradeoffs.',
        },
        {
            'title': 'Genome Forge now teaches uncertainty as a first-class sequence state',
            'value': f'EGFP ambiguity training record carries {sum(1 for ch in ambiguous if ch not in "ACGT")} explicit unresolved positions',
            'story': 'That matters because real assay design and identity search often start before every position is perfectly resolved. Good workflows preserve uncertainty instead of flattening it away.',
        },
        {
            'title': 'Annotation transfer turns familiar parts into reusable evidence',
            'value': 'EGFP reference features can now transfer into a candidate plasmid by similarity',
            'story': 'This mirrors a beloved Geneious-style workflow: a known part appears in a new construct, and useful feature labels follow only when identity and coverage support the transfer.',
        },
        {
            'title': 'Multi-read Sanger consensus now separates expected edits from surprises',
            'value': 'Consensus reports variants, disagreements, genotype checks, and a final verdict',
            'story': 'The tutorial now asks students to confirm an expected reporter variant while still flagging unexpected sequence changes. That is closer to real construct verification than trusting one base-called read.',
        },
        {
            'title': 'Selected-sequence launch bridges local work to public search',
            'value': 'NCBI and WormBase launch workflows are covered as explicit training cases',
            'story': 'The new lesson emphasizes provenance: search exactly the selected region, keep the FASTA header informative, and interpret public hits in the context of the local record.',
        },
    ]


def render_featured_results() -> str:
    cards = ''.join(
        dedent(f'''
        <div class="card">
          <h3>{escape(row["title"])}</h3>
          <p class="metric">{escape(row["value"])}</p>
          <p>{escape(row["story"])}</p>
        </div>
        ''').strip()
        for row in compute_featured_results()
    )
    return f'<div class="cards cards-wide">{cards}</div>'


def render_visual_gallery() -> str:
    figures = ''.join(
        dedent(f'''
        <div class="figure-card">
          <img src="{escape(row["file"])}" alt="{escape(row["title"])}" />
          <div>
            <h3>{escape(row["title"])}</h3>
            <p>{escape(row["caption"])}</p>
          </div>
        </div>
        ''').strip()
        for row in FEATURE_GALLERY
    )
    return f'<div class="gallery">{figures}</div>'


def render_concept_gallery() -> str:
    figures = ''.join(
        dedent(f'''
        <div class="figure-card concept-card">
          <img src="{escape(row["file"])}" alt="{escape(row["title"])}" />
          <div>
            <h3>{escape(row["title"])}</h3>
            <p>{escape(row["caption"])}</p>
          </div>
        </div>
        ''').strip()
        for row in CONCEPT_ILLUSTRATIONS.values()
    )
    return f'<div class="gallery concept-gallery">{figures}</div>'


def render_cover_spread() -> str:
    showcase_ids = ['A', 'AH', 'AJ', 'AL']
    cards = ''.join(
        dedent(f'''
        <div class="cover-shot">
          <img src="{escape(FLAGSHIP_SCREENSHOTS[case_id]["file"])}" alt="{escape(FLAGSHIP_SCREENSHOTS[case_id]["title"])}" />
          <div class="cover-shot-text">
            <b>Case {escape(case_id)}</b>
            <span>{escape(FLAGSHIP_SCREENSHOTS[case_id]["title"])}</span>
          </div>
        </div>
        ''').strip()
        for case_id in showcase_ids
    )
    return f'<div class="cover-spread">{cards}</div>'


def render_cover_art() -> str:
    return dedent('''
      <svg class="cover-art" viewBox="0 0 760 620" role="img" aria-label="Abstract DNA orbit, plasmid circle, and sequence constellation">
        <defs>
          <radialGradient id="coverGlow" cx="50%" cy="42%" r="62%">
            <stop offset="0%" stop-color="#f8e8b0" stop-opacity="0.74" />
            <stop offset="42%" stop-color="#46d2c6" stop-opacity="0.22" />
            <stop offset="100%" stop-color="#0a1723" stop-opacity="0" />
          </radialGradient>
          <linearGradient id="coverHelix" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#f7d28a" />
            <stop offset="48%" stop-color="#72e0d4" />
            <stop offset="100%" stop-color="#e99bb6" />
          </linearGradient>
          <linearGradient id="coverRing" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#e7c37b" stop-opacity="0.95" />
            <stop offset="55%" stop-color="#5ed3cb" stop-opacity="0.85" />
            <stop offset="100%" stop-color="#f1f5f9" stop-opacity="0.70" />
          </linearGradient>
          <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#020711" flood-opacity="0.35" />
          </filter>
        </defs>
        <rect x="0" y="0" width="760" height="620" fill="url(#coverGlow)" />
        <g opacity="0.22" stroke="#b6d7d8" stroke-width="1">
          <path d="M70 92 C190 38 306 156 444 102 S640 58 720 130" fill="none" />
          <path d="M54 515 C202 404 314 594 474 466 S640 402 728 480" fill="none" />
          <path d="M80 178 H692 M112 245 H704 M64 392 H682" stroke-dasharray="2 14" />
        </g>
        <g transform="translate(88 68)" filter="url(#softShadow)">
          <circle cx="296" cy="256" r="182" fill="none" stroke="url(#coverRing)" stroke-width="18" opacity="0.90" />
          <path d="M296 74 A182 182 0 0 1 478 256" fill="none" stroke="#f3c66f" stroke-width="28" stroke-linecap="round" opacity="0.55" />
          <path d="M116 272 A182 182 0 0 1 296 74" fill="none" stroke="#4fd0c6" stroke-width="12" stroke-linecap="round" opacity="0.62" />
          <path d="M296 438 A182 182 0 0 1 126 318" fill="none" stroke="#d97398" stroke-width="10" stroke-linecap="round" opacity="0.64" />
        </g>
        <g transform="translate(132 116)" fill="none" stroke="url(#coverHelix)" stroke-width="6" stroke-linecap="round">
          <path d="M0 160 C80 40 160 40 240 160 S400 280 480 160" />
          <path d="M0 260 C80 380 160 380 240 260 S400 140 480 260" />
        </g>
        <g transform="translate(136 116)" stroke="#f8f3e8" stroke-width="2.4" stroke-linecap="round" opacity="0.78">
          <path d="M24 170 L24 250" />
          <path d="M78 114 L78 306" />
          <path d="M132 86 L132 334" />
          <path d="M186 110 L186 310" />
          <path d="M240 170 L240 250" />
          <path d="M294 226 L294 194" />
          <path d="M348 300 L348 120" />
          <path d="M402 328 L402 92" />
          <path d="M456 298 L456 122" />
        </g>
        <g fill="#f8f3e8" opacity="0.94">
          <circle cx="126" cy="88" r="3.4" />
          <circle cx="180" cy="468" r="2.8" />
          <circle cx="614" cy="128" r="3.8" />
          <circle cx="678" cy="386" r="2.4" />
          <circle cx="528" cy="512" r="3.2" />
          <circle cx="84" cy="334" r="2.7" />
        </g>
        <g font-family="IBM Plex Mono, Menlo, Consolas, monospace" font-size="19" fill="#f7ead0" opacity="0.78">
          <text x="102" y="552">ATG</text>
          <text x="604" y="92">GFP</text>
          <text x="640" y="536">BRAF</text>
          <text x="64" y="250">lacZ</text>
        </g>
      </svg>
    ''').strip()


def render_front_cover(case_count: int) -> str:
    return dedent(f'''
      <section class="cover book-cover" aria-label="Front cover">
        <div class="cover-topline">
          <span>Genome Forge {escape(APP_VERSION)}</span>
          <span>Textbook Edition</span>
        </div>
        <div class="cover-hero">
          <div class="cover-copy">
            <p class="cover-kicker">Self-study with real molecular data</p>
            <h1>{escape(TUTORIAL_TITLE)}</h1>
            <p class="cover-deck">{escape(TUTORIAL_SUBTITLE)}.</p>
          </div>
          <div class="cover-art-wrap">{render_cover_art()}</div>
        </div>
        <div class="cover-lower">
          <p class="cover-thesis">Not button memorization. A guided apprenticeship in reading molecules, designing assays, interrogating evidence, and packaging work someone else can trust.</p>
          <div class="cover-stats">
            <div><b>{case_count}</b><span>lessons</span></div>
            <div><b>Real</b><span>records</span></div>
            <div><b>Letter</b><span>print edition</span></div>
          </div>
        </div>
        <div class="cover-footer">
          <span>{escape(TUTORIAL_AUTHOR)}</span>
          <span>{escape(TODAY)}</span>
        </div>
      </section>
    ''').strip()


def render_inside_front_cover(case_count: int) -> str:
    return dedent(f'''
      <section class="inside-cover" aria-label="Inside front cover">
        <div class="inside-cover-orbit" aria-hidden="true">
          <svg viewBox="0 0 520 520" role="img" aria-label="Subtle molecular study compass">
            <defs>
              <linearGradient id="insideOrbit" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#f0c36e" stop-opacity="0.72" />
                <stop offset="52%" stop-color="#47c6bd" stop-opacity="0.72" />
                <stop offset="100%" stop-color="#d987a5" stop-opacity="0.60" />
              </linearGradient>
            </defs>
            <circle cx="260" cy="260" r="150" fill="none" stroke="url(#insideOrbit)" stroke-width="8" opacity="0.34" />
            <circle cx="260" cy="260" r="90" fill="none" stroke="#17324a" stroke-width="1.4" opacity="0.18" />
            <path d="M92 274 C160 170 228 356 306 224 S436 192 480 270" fill="none" stroke="#146c72" stroke-width="4" stroke-linecap="round" opacity="0.32" />
            <path d="M92 234 C166 336 224 150 308 292 S438 332 480 252" fill="none" stroke="#a56b14" stroke-width="4" stroke-linecap="round" opacity="0.30" />
          </svg>
        </div>
        <div class="inside-cover-copy">
          <p class="inside-kicker">Duplex Print Edition</p>
          <h2>A laboratory notebook for the computational imagination.</h2>
          <p>This volume is designed for two-sided reading: covers outside, generous inner gutters inside, and major clusters opening on recto pages.</p>
          <div class="inside-cover-grid">
            <span>Read the molecule before the menu.</span>
            <span>Ask what decision the output supports.</span>
            <span>Keep coordinates, evidence, and interpretation together.</span>
            <span>Leave a trail another scientist can reopen.</span>
          </div>
          <p class="inside-cover-note">{case_count} lessons. Real records. Reproducible sample data.</p>
        </div>
      </section>
    ''').strip()


def render_back_cover(case_count: int) -> str:
    return dedent(f'''
      <section class="back-cover" aria-label="Back cover">
        <div class="back-cover-mark" aria-hidden="true">
          <svg viewBox="-24 0 568 520" role="img" aria-label="Abstract molecule compass">
            <defs>
              <linearGradient id="backRing" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#f0c36e" />
                <stop offset="56%" stop-color="#47c6bd" />
                <stop offset="100%" stop-color="#d987a5" />
              </linearGradient>
            </defs>
            <circle cx="260" cy="260" r="174" fill="none" stroke="url(#backRing)" stroke-width="14" opacity="0.36" />
            <circle cx="260" cy="260" r="118" fill="none" stroke="#d7eceb" stroke-width="1.5" opacity="0.42" />
            <path d="M84 300 C168 184 250 390 340 214 S468 198 492 274" fill="none" stroke="#f0c36e" stroke-width="5" stroke-linecap="round" opacity="0.58" />
            <path d="M92 224 C182 352 250 146 346 314 S462 326 492 246" fill="none" stroke="#5ed3cb" stroke-width="5" stroke-linecap="round" opacity="0.62" />
            <g stroke="#f8f3e8" stroke-width="1.7" opacity="0.44">
              <path d="M130 250 L130 278" /><path d="M172 242 L172 286" /><path d="M214 224 L214 304" />
              <path d="M256 244 L256 284" /><path d="M298 226 L298 306" /><path d="M340 238 L340 290" />
              <path d="M382 244 L382 282" />
            </g>
          </svg>
        </div>
        <div class="back-copy">
          <p class="back-kicker">Genome Forge DNA Tutorial</p>
          <h2>Learn the living logic behind sequence analysis.</h2>
          <p>This book teaches DNA bioinformatics as a way of thinking: identify the biological object, choose the experiment, inspect the evidence, and make the interpretation reproducible.</p>
          <p>The lessons use real-world molecular records, including EGFP, mCherry, pUC19/lacZ logic, and a BRAF exon 15 hotspot fragment. Training derivatives are marked as such and exist to make comparison, ambiguity, and assay-design questions concrete.</p>
          <div class="back-promises">
            <span>Map and annotate DNA</span>
            <span>Design primers, digests, and edits</span>
            <span>Read traces and alignments</span>
            <span>Package reproducible evidence</span>
          </div>
        </div>
        <div class="back-bottom">
          <div>
            <b>{case_count} lessons · sample data included</b>
            <span>HTML and PDF generated from repository source.</span>
          </div>
          <div class="back-repo">
            <span>{escape(REPO_URL)}</span>
            <span>Apache License 2.0 · {escape(APP_VERSION)}</span>
          </div>
        </div>
      </section>
    ''').strip()


def render_learning_path(case_count: int) -> str:
    stages = [
        ('I', 'Read the molecule', 'Map, annotate, translate, and decide what kind of biological object is in front of you.'),
        ('II', 'Design the experiment', 'Choose primers, enzymes, assemblies, and edits with the failure modes visible.'),
        ('III', 'Interrogate evidence', 'Use traces, alignments, search, coverage, and ambiguity codes to decide what the data support.'),
        ('IV', 'Package the work', 'Preserve projects, reviews, share bundles, and explanations so someone else can continue cleanly.'),
    ]
    cards = ''.join(
        dedent(f'''
        <div class="path-step">
          <span>{escape(number)}</span>
          <h3>{escape(title)}</h3>
          <p>{escape(text)}</p>
        </div>
        ''').strip()
        for number, title, text in stages
    )
    return dedent(f'''
      <div class="learning-path" aria-label="Tutorial learning path">
        <div class="path-intro">
          <p class="section-kicker">Course Arc</p>
          <h3>{case_count} lessons, one practical reasoning loop</h3>
          <p>Each case is designed to move from software action to biological claim. The point is not button memorization; it is learning how sequence evidence changes an experimental decision.</p>
        </div>
        <div class="path-steps">{cards}</div>
      </div>
    ''').strip()


def render_publication_note(case_count: int) -> str:
    return dedent(f'''
      <section class="section frontmatter">
        <p class="section-kicker">Front Matter</p>
        <h2>Publication Notes</h2>
        <div class="pub-grid">
          <div class="card">
            <h3>Abstract</h3>
            <p>This volume teaches practical DNA bioinformatics with Genome Forge through real biological records, stepwise software workflows, expected outputs, interpretation guidance, and biological explanation in one reproducible text.</p>
            <p>The current edition contains {case_count} lessons organized into clusters that move from molecular architecture and restriction logic to assay design, assembly, comparative reasoning, ambiguity-aware analysis, and reproducible project delivery.</p>
          </div>
          <div class="card alt">
            <h3>Edition and Citation</h3>
            <p><b>Edition:</b> Genome Forge Textbook Edition, generated from repository source on <code>{escape(TODAY)}</code>.</p>
            <p><b>Preferred citation:</b> <i>{escape(TUTORIAL_TITLE)}</i>, Genome Forge {escape(APP_VERSION)}, tutorial edition.</p>
            <p><b>Formats:</b> HTML and PDF are generated from the same source so case numbering, sample data, and screenshots stay aligned.</p>
          </div>
        </div>
      </section>
    ''').strip()


def render_half_title_page() -> str:
    return dedent(f'''
      <section class="half-title-page" aria-label="Half title page">
        <p class="half-title-kicker">Genome Forge DNA Tutorial</p>
        <h1 class="half-title">{escape(TUTORIAL_TITLE)}</h1>
        <p class="half-subtitle">{escape(TUTORIAL_SUBTITLE)}</p>
      </section>
    ''').strip()


def render_imprint_page(case_count: int) -> str:
    return dedent(f'''
      <section class="imprint-page" aria-label="Imprint page">
        <div class="imprint-box">
          <p class="section-kicker">Imprint</p>
          <h2 class="imprint-title">Edition and Copyright</h2>
          <p><b>Title:</b> <i>{escape(TUTORIAL_TITLE)}</i></p>
          <p><b>Edition:</b> Genome Forge {escape(APP_VERSION)} textbook edition generated on <code>{escape(TODAY)}</code>.</p>
          <p><b>Authoring body:</b> {escape(TUTORIAL_AUTHOR)}</p>
          <p><b>Repository:</b> <a href="{escape(REPO_URL)}">{escape(REPO_URL)}</a></p>
          <p><b>License:</b> Apache License 2.0 for the project source. Public-source records and clearly labelled training derivatives are documented in the bundled dataset metadata.</p>
          <p><b>Scope:</b> This volume contains {case_count} lessons, real-world sample data, and HTML/PDF outputs rebuilt from the same source tutorial.</p>
          <p><b>Suggested citation:</b> {escape(TUTORIAL_AUTHOR)}. <i>{escape(TUTORIAL_TITLE)}</i>. Genome Forge {escape(APP_VERSION)}. {escape(COPYRIGHT_YEAR)}.</p>
          <p class="muted">Copyright © {escape(COPYRIGHT_YEAR)} {escape(TUTORIAL_AUTHOR)}.</p>
        </div>
      </section>
    ''').strip()


def render_toc() -> str:
    groups = []
    for cluster in CLUSTERS:
        case_entries = ''.join(
            f'<a class="toc-entry toc-case" href="#case-{escape(case_info["id"])}"><span class="toc-entry-title">Case {escape(case_info["id"])}: {escape(case_info["title"])}</span></a>'
            for case_info in CLUSTER_CASES[cluster['id']]
        )
        groups.append(dedent(f'''
          <div class="toc-group">
            <a class="toc-entry toc-cluster" href="#cluster-{escape(cluster["id"])}">
              <span class="toc-entry-title">Cluster {escape(cluster["id"])}: {escape(cluster["title"])}</span>
              <span class="toc-count">{len(CLUSTER_CASES[cluster["id"]])} cases</span>
            </a>
            <div class="toc-subentries">{case_entries}</div>
          </div>
        ''').strip())
    return '<div class="toc-groups">' + ''.join(groups) + '</div>'


def render_iupac_table() -> str:
    rows = ''.join(
        '<tr>'
        f'<td><code>{escape(code)}</code></td>'
        f'<td>{escape(bases)}</td>'
        f'<td>{escape(name)}</td>'
        f'<td>{escape(use)}</td>'
        '</tr>'
        for code, bases, name, use in IUPAC_GUIDE
    )
    return (
        '<table>'
        '<thead><tr><th>Code</th><th>Allowed base(s)</th><th>Meaning</th><th>Why you would keep it</th></tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table>'
    )


def render_case_screenshot(case_id: str) -> str:
    shot = FLAGSHIP_SCREENSHOTS.get(case_id)
    if not shot:
        return ''
    return dedent(f'''
      <div class="figure ui-shot">
        <img src="{escape(shot["file"])}" alt="{escape(shot["title"])}" />
        <p class="caption"><b>{escape(shot["title"])}</b>. {escape(shot["caption"])}</p>
      </div>
    ''').strip()


def render_case_concept_illustration(case_id: str) -> str:
    shot = CONCEPT_ILLUSTRATIONS.get(case_id)
    if not shot:
        return ''
    return dedent(f'''
      <div class="figure concept">
        <img src="{escape(shot["file"])}" alt="{escape(shot["title"])}" />
        <p class="caption"><b>{escape(shot["title"])}</b>. {escape(shot["caption"])}</p>
      </div>
    ''').strip()


def render_case(case_info: dict) -> str:
    records = case_info['records']
    record_details = ' '.join(RECORDS[name]['input_details'] for name in records)
    starter_values = case_info.get('starter_values', [])
    expected = case_info['expected']
    interpretation = case_info['interpretation']
    concept_html = render_case_concept_illustration(case_info['id'])
    screenshot_html = render_case_screenshot(case_info['id'])
    starter_html = ''
    if starter_values:
        starter_html = f'<div class="study-note"><b>Starter Values</b><ul>{format_list(starter_values, escape_items=False)}</ul></div>'
    return dedent(f'''
      <article class="case" id="case-{escape(case_info['id'])}">
        <div class="case-head">
          <div>
            <p class="eyebrow">Case {escape(case_info['id'])} · Cluster {escape(case_info['cluster'])}</p>
            <h3 class="case-title">Case {escape(case_info['id'])}: {escape(case_info['title'])}</h3>
            <p class="lead">{escape(case_info['biological_question'])}</p>
          </div>
          <div class="case-meta">
            <div><b>Tab</b><span>{escape(case_info['tab'])}</span></div>
            <div><b>Workflow</b><span>{escape(case_info['workflow'])}</span></div>
            <div><b>Records</b><span>{render_record_badges(records)}</span></div>
            <div><b>APIs</b><span>{' '.join(f'<code>{escape(api)}</code>' for api in case_info['apis'])}</span></div>
          </div>
        </div>
        <div class="case-grid">
          <div class="card narrative">
            <h4>Why This Case Matters</h4>
            <p>{escape(case_info['data_details'])}</p>
            <p>{escape(case_info['biology'])}</p>
          </div>
          <div class="card narrative alt">
            <h4>Input Data Explained</h4>
            <p>{escape(record_details)}</p>
            <p>{escape(case_info['fun_fact'])}</p>
          </div>
        </div>
        {starter_html}
        {render_case_glossary(case_info)}
        {render_exact_ui_steps(case_info)}
        {concept_html}
        {screenshot_html}
        <div class="resultbox"><b>Sample Results</b><p class="muted">Representative output shaped around the bundled real-world record(s) or their documented training derivatives. Values are rounded for readability, but the biological story is tied to the included data.</p><pre>{format_json_block(case_info['sample_result'])}</pre></div>
        <div class="expected"><b>Expected Results</b><ul>{format_list(expected)}</ul></div>
        <div class="interpret"><b>How to Interpret the Results</b><ul>{format_list(interpretation)}</ul></div>
        {render_evidence_inference(case_info)}
        {render_decision_card(case_info)}
        {render_common_mistakes(case_info)}
        {render_lab_chief_checklist(case_info)}
        <div class="biology"><b>Biological Explanation</b><p>{escape(case_info['biology'])}</p><p><b>Fun fact from this example:</b> {escape(case_info['fun_fact'])}</p></div>
      </article>
    ''').strip()


def render_cluster(cluster: dict) -> str:
    cluster_case_strip = ''.join(
        f'<span class="case-chip">Case {escape(case_info["id"])} · {escape(case_info["title"])}</span>'
        for case_info in CLUSTER_CASES[cluster['id']]
    )
    cases_html = '\n'.join(render_case(case_info) for case_info in CLUSTER_CASES[cluster['id']])
    return dedent(f'''
      <section class="section cluster" id="cluster-{escape(cluster['id'])}">
        <div class="chapter-opener print-only" aria-label="Cluster {escape(cluster['id'])} opener">
          <p class="section-kicker">Cluster {escape(cluster['id'])}</p>
          <h2 class="chapter-title">Cluster {escape(cluster['id'])}: {escape(cluster['title'])}</h2>
          <p class="chapter-theme">{escape(cluster['theme'])}</p>
          <div class="chapter-opener-grid">
            <div class="chapter-summary">
              <h3>Lessons in This Cluster</h3>
              <div class="chapter-case-strip">{cluster_case_strip}</div>
            </div>
            <div class="chapter-figure figure narrow">
              <img src="{escape(cluster['figure'])}" alt="{escape(cluster['title'])}" />
              <p class="caption">{escape(cluster['caption'])}</p>
            </div>
          </div>
        </div>
        <div class="cluster-head">
          <div>
            <p class="eyebrow">Cluster {escape(cluster['id'])}</p>
            <h2 class="cluster-title">Cluster {escape(cluster['id'])}: {escape(cluster['title'])}</h2>
            <p class="muted">{escape(cluster['theme'])}</p>
            <div class="case-strip">{cluster_case_strip}</div>
          </div>
          <div class="cluster-figure figure narrow">
            <img src="{escape(cluster['figure'])}" alt="{escape(cluster['title'])}" />
            <p class="caption">{escape(cluster['caption'])}</p>
          </div>
        </div>
        {render_cluster_checkpoint(cluster)}
        {cases_html}
      </section>
    ''').strip()


def render_html() -> str:
    toc_html = render_toc()
    cluster_sections = '\n'.join(render_cluster(cluster) for cluster in CLUSTERS)
    case_count = len(CASES)
    return dedent(f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="author" content="{escape(TUTORIAL_AUTHOR)}" />
  <meta name="description" content="Publication-style self-study DNA bioinformatics tutorial for Genome Forge using real biological records, sequence workflows, cloning design, molecular evidence, and biological interpretation." />
  <meta name="keywords" content="DNA bioinformatics, sequence analysis, cloning, plasmid, molecular evidence, genome forge, tutorial, molecular biology" />
  <meta name="generator" content="Genome Forge tutorial generator" />
  <meta name="dcterms.created" content="{escape(TODAY)}" />
  <meta name="dcterms.modified" content="{escape(TODAY)}" />
  <title>{escape(TUTORIAL_TITLE)} ({escape(APP_VERSION)})</title>
  <style>
    @page {{
      size: Letter;
      margin: 0.68in 0.60in 0.78in 0.60in;
    }}
    @page :left {{
      margin-left: 0.55in;
      margin-right: 0.78in;
      @top-left {{
        content: "{escape(TUTORIAL_TITLE)}";
        color: #6b7280;
        font-size: 8.5px;
        letter-spacing: 0.06em;
      }}
      @bottom-left {{
        content: counter(page);
        color: #64748b;
        font-size: 9px;
      }}
    }}
    @page :right {{
      margin-left: 0.78in;
      margin-right: 0.55in;
      @top-right {{
        content: "Genome Forge DNA Tutorial";
        color: #6b7280;
        font-size: 8.5px;
        letter-spacing: 0.06em;
      }}
      @bottom-right {{
        content: counter(page);
        color: #64748b;
        font-size: 9px;
      }}
    }}
    @page :first {{
      @top-left {{ content: none; }}
      @top-right {{ content: none; }}
      @bottom-left {{ content: none; }}
      @bottom-right {{ content: none; }}
    }}
    @page cover {{
      size: Letter;
      margin: 0;
      @top-left {{ content: none; }}
      @top-right {{ content: none; }}
      @bottom-left {{ content: none; }}
      @bottom-right {{ content: none; }}
    }}
    @page backcover {{
      size: Letter;
      margin: 0;
      @top-left {{ content: none; }}
      @top-right {{ content: none; }}
      @bottom-left {{ content: none; }}
      @bottom-right {{ content: none; }}
    }}
    @page insidecover {{
      size: Letter;
      margin: 0;
      @top-left {{ content: none; }}
      @top-right {{ content: none; }}
      @bottom-left {{ content: none; }}
      @bottom-right {{ content: none; }}
    }}
    @page :blank {{
      @top-left {{ content: none; }}
      @top-right {{ content: none; }}
      @bottom-left {{ content: none; }}
      @bottom-right {{ content: none; }}
    }}
    @page pretitle {{
      @top-left {{ content: none; }}
      @top-right {{ content: none; }}
      @bottom-left {{ content: none; }}
      @bottom-right {{ content: none; }}
    }}
    @page imprint {{
      @top-left {{ content: none; }}
      @top-right {{ content: none; }}
      @bottom-left {{ content: none; }}
      @bottom-right {{ content: none; }}
    }}
    :root {{
      --ink: #17202a;
      --muted: #526170;
      --line: #c9d5df;
      --panel: #f7fafc;
      --panel-strong: #eef6f7;
      --navy: #17324a;
      --teal: #146c72;
      --gold: #a56b14;
      --rose: #8c4161;
      --paper: #ffffff;
      --shadow: 0 10px 26px rgba(20, 39, 54, 0.07);
      --code-bg: #0b1220;
      --code-ink: #dbeafe;
      --rule: linear-gradient(90deg, #146c72, #a56b14, #8c4161);
    }}
    * {{ box-sizing: border-box; }}
    html {{ hyphens: auto; }}
    body {{
      margin: 0;
      background: #edf3f6;
      color: var(--ink);
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
      font-size: 11.5px;
      line-height: 1.66;
      counter-reset: figure;
    }}
    a {{ color: var(--teal); text-decoration: none; }}
    p, li {{ widows: 3; orphans: 3; }}
    code {{
      font-family: "IBM Plex Mono", Menlo, Consolas, monospace;
      background: #e9f1f5;
      color: #14344d;
      padding: 2px 5px;
      border-radius: 4px;
      font-size: 10.7px;
    }}
    pre {{
      margin: 8px 0 0;
      padding: 10px 12px;
      border-radius: 8px;
      background: var(--code-bg);
      color: var(--code-ink);
      font-family: "IBM Plex Mono", Menlo, Consolas, monospace;
      font-size: 10.2px;
      line-height: 1.45;
      white-space: pre-wrap;
      page-break-inside: avoid;
    }}
    .doc {{ max-width: 940px; margin: 0 auto; padding: 20px 14px 44px; }}
    .half-title-page {{
      page: pretitle;
      min-height: 9.05in;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      padding: 0.45in 0.40in;
      break-after: page;
    }}
    .half-title-kicker {{
      margin: 0 0 0.38in;
      color: var(--gold);
      text-transform: uppercase;
      letter-spacing: 0.18em;
      font-size: 10px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .half-title {{
      margin: 0;
      max-width: 600px;
      color: var(--navy);
      font-size: 28px;
      line-height: 1.12;
      font-family: "Baskerville", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
    }}
    .half-subtitle {{
      margin: 0.38in 0 0;
      max-width: 520px;
      color: var(--muted);
      font-size: 12px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .cover {{
      page: cover;
      break-after: page;
      position: relative;
      overflow: hidden;
      padding: 26px 26px 22px;
      border-radius: 12px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247, 251, 252, 0.98)),
        linear-gradient(135deg, #ffffff 0%, #edf7f8 100%);
      color: var(--ink);
      box-shadow: var(--shadow);
      margin-bottom: 12px;
      border: 1px solid #cbd9e2;
    }}
    .cover::before {{
      content: "";
      position: absolute;
      inset: 0 0 auto 0;
      height: 6px;
      background: var(--rule);
    }}
    .cover h1 {{
      margin: 4px 0 10px;
      font-family: "Baskerville", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: 33px;
      line-height: 1.05;
      max-width: 720px;
      color: var(--navy);
    }}
    .cover p {{ margin: 8px 0; max-width: 720px; }}
    .cover .deck {{
      max-width: 700px;
      font-size: 13px;
      color: #344454;
    }}
    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 10.5px;
      font-weight: 700;
      opacity: 0.9;
      margin: 0;
      color: var(--gold);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .meta {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }}
    .meta .k {{
      border: 1px solid #cbd9e2;
      border-radius: 8px;
      background: rgba(255,255,255,0.82);
      padding: 9px 10px;
      font-size: 10px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .meta .k b {{ display: block; margin-top: 4px; font-size: 12px; color: var(--navy); }}
    .imprint-page {{
      page: imprint;
      min-height: 9.05in;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0.38in 0;
      break-after: page;
    }}
    .imprint-box {{
      width: 100%;
      max-width: 760px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: linear-gradient(180deg, #ffffff, #f3f8fa);
      padding: 18px 20px;
      box-shadow: var(--shadow);
    }}
    .imprint-title {{
      margin: 0 0 8px;
      color: var(--navy);
      font-size: 22px;
      font-family: "Baskerville", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
    }}
    .cover-note {{
      margin-top: 14px;
      padding-top: 10px;
      border-top: 1px solid rgba(20, 108, 114, 0.22);
      max-width: 720px;
      color: #4c5966;
      font-size: 10.7px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .cover-spread {{
      margin-top: 14px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .cover-shot {{
      border-radius: 8px;
      overflow: hidden;
      background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(241,247,249,0.98));
      border: 1px solid #cbd9e2;
      box-shadow: 0 10px 22px rgba(20, 39, 54, 0.08);
    }}
    .cover-shot img {{
      width: 100%;
      display: block;
      aspect-ratio: 1.22 / 1;
      object-fit: cover;
      background: #edf4f7;
    }}
    .cover-shot-text {{
      padding: 10px 12px 12px;
      display: grid;
      gap: 4px;
      font-size: 10.6px;
      color: var(--muted);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .cover-shot-text b {{
      color: var(--navy);
      font-size: 10px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .book-cover {{
      min-height: 11in;
      border: 0;
      border-radius: 0;
      margin: 0;
      padding: 0.62in 0.70in 0.54in;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      color: #f7f1df;
      background:
        radial-gradient(circle at 76% 24%, rgba(80, 210, 198, 0.24), rgba(80, 210, 198, 0) 34%),
        radial-gradient(circle at 15% 82%, rgba(217, 115, 152, 0.22), rgba(217, 115, 152, 0) 32%),
        linear-gradient(142deg, #07131f 0%, #0f2635 48%, #13383b 100%);
      box-shadow: none;
    }}
    .book-cover * {{
      hyphens: none;
    }}
    .book-cover::before {{
      content: "";
      position: absolute;
      inset: 0.28in auto 0.28in 0.28in;
      width: 0.08in;
      height: auto;
      background: linear-gradient(180deg, #f0c36e, #50d2c6, #d97398);
      border-radius: 999px;
      opacity: 0.92;
    }}
    .book-cover::after {{
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(90deg, rgba(255,255,255,0.055) 1px, transparent 1px),
        linear-gradient(0deg, rgba(255,255,255,0.040) 1px, transparent 1px);
      background-size: 0.48in 0.48in;
      mask-image: linear-gradient(120deg, transparent 0%, black 22%, black 72%, transparent 100%);
      opacity: 0.34;
    }}
    .cover-topline, .cover-footer {{
      position: relative;
      z-index: 1;
      display: flex;
      justify-content: space-between;
      gap: 20px;
      color: rgba(247, 241, 223, 0.78);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 10px;
      letter-spacing: 0.13em;
      text-transform: uppercase;
    }}
    .cover-hero {{
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: 0.94fr 1.06fr;
      gap: 0.34in;
      align-items: center;
      margin-top: 0.20in;
    }}
    .cover-copy {{
      align-self: center;
    }}
    .cover-kicker {{
      margin: 0 0 0.18in;
      color: #f0c36e;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.17em;
      text-transform: uppercase;
    }}
    .book-cover h1 {{
      margin: 0;
      max-width: 4.3in;
      color: #fffaf0;
      font-family: "Baskerville", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: 48px;
      line-height: 0.98;
      letter-spacing: -0.035em;
    }}
    .cover-deck {{
      margin: 0.22in 0 0;
      max-width: 3.95in;
      color: rgba(247, 241, 223, 0.84);
      font-size: 14px;
      line-height: 1.55;
    }}
    .cover-art-wrap {{
      min-height: 4.7in;
      display: grid;
      place-items: center;
    }}
    .cover-art {{
      width: 100%;
      max-width: 4.42in;
      height: auto;
      display: block;
    }}
    .cover-lower {{
      position: relative;
      z-index: 1;
      display: block;
      margin-top: 0.18in;
      padding-top: 0.24in;
      border-top: 1px solid rgba(247, 241, 223, 0.26);
    }}
    .cover-thesis {{
      margin: 0;
      max-width: 6.35in;
      color: rgba(247, 241, 223, 0.78);
      font-size: 11.6px;
      line-height: 1.55;
    }}
    .cover-stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.18in;
      margin-top: 0.20in;
    }}
    .cover-stats div {{
      display: inline-flex;
      align-items: baseline;
      gap: 0.07in;
      border: 0;
      border-left: 0.035in solid rgba(80, 210, 198, 0.75);
      background: transparent;
      padding: 0 0 0 0.09in;
    }}
    .cover-stats b {{
      display: block;
      color: #fffaf0;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 14px;
      line-height: 1.05;
      white-space: nowrap;
    }}
    .cover-stats span {{
      display: inline;
      margin-top: 0;
      color: rgba(247, 241, 223, 0.66);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 8.4px;
      line-height: 1.25;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      overflow-wrap: normal;
      word-break: normal;
      white-space: nowrap;
    }}
    .back-cover {{
      page: backcover;
      break-before: left;
      position: relative;
      overflow: hidden;
      min-height: 11in;
      padding: 0.66in 0.72in 0.56in;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      color: #f7f1df;
      background:
        radial-gradient(circle at 18% 20%, rgba(240, 195, 110, 0.20), rgba(240, 195, 110, 0) 30%),
        radial-gradient(circle at 84% 70%, rgba(80, 210, 198, 0.18), rgba(80, 210, 198, 0) 32%),
        linear-gradient(160deg, #06111c 0%, #0a1f2d 54%, #142f32 100%);
    }}
    .inside-cover {{
      page: insidecover;
      break-after: page;
      position: relative;
      overflow: hidden;
      min-height: 11in;
      padding: 0.78in 0.82in;
      display: flex;
      align-items: center;
      color: var(--navy);
      background:
        radial-gradient(circle at 82% 26%, rgba(20, 108, 114, 0.13), rgba(20, 108, 114, 0) 34%),
        radial-gradient(circle at 14% 84%, rgba(165, 107, 20, 0.12), rgba(165, 107, 20, 0) 32%),
        linear-gradient(135deg, #f9f4e8 0%, #f4f8f8 58%, #edf5f2 100%);
    }}
    .inside-cover * {{
      hyphens: none;
      overflow-wrap: normal;
    }}
    .inside-cover::before {{
      content: "";
      position: absolute;
      inset: 0.42in;
      border: 1px solid rgba(23, 50, 74, 0.13);
      pointer-events: none;
    }}
    .inside-cover-orbit {{
      position: absolute;
      right: -0.45in;
      top: 0.55in;
      width: 4.15in;
      opacity: 0.85;
    }}
    .inside-cover-orbit svg {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .inside-cover-copy {{
      position: relative;
      z-index: 1;
      max-width: 4.92in;
    }}
    .inside-kicker {{
      margin: 0 0 0.16in;
      color: var(--gold);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.15em;
      text-transform: uppercase;
    }}
    .inside-cover h2 {{
      margin: 0 0 0.24in;
      max-width: 4.6in;
      color: var(--navy);
      font-family: "Baskerville", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: 32px;
      line-height: 1.05;
      letter-spacing: -0.02em;
    }}
    .inside-cover p {{
      margin: 0 0 0.18in;
      color: #405463;
      font-size: 12.3px;
      line-height: 1.6;
    }}
    .inside-cover-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 0.10in;
      margin: 0.30in 0;
      max-width: 4.85in;
    }}
    .inside-cover-grid span {{
      border-left: 0.035in solid var(--teal);
      background: rgba(255,255,255,0.55);
      padding: 0.12in 0.14in;
      color: #17324a;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 10.7px;
      font-weight: 700;
      line-height: 1.35;
    }}
    .inside-cover-note {{
      margin-top: 0.28in;
      color: #6b5c3f;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 10px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .back-cover::before {{
      content: "";
      position: absolute;
      inset: 0.42in 0.42in;
      border: 1px solid rgba(247, 241, 223, 0.20);
      pointer-events: none;
      display: none;
    }}
    .back-cover-mark {{
      position: absolute;
      right: 0.42in;
      top: 0.55in;
      width: 3.12in;
      opacity: 0.82;
    }}
    .back-cover-mark svg {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .back-copy {{
      position: relative;
      z-index: 1;
      max-width: 5.15in;
      margin-top: 1.04in;
    }}
    .back-kicker {{
      margin: 0 0 0.18in;
      color: #f0c36e;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.17em;
      text-transform: uppercase;
    }}
    .back-cover h2 {{
      margin: 0 0 0.22in;
      max-width: 4.70in;
      color: #fffaf0;
      font-family: "Baskerville", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
      font-size: 31px;
      line-height: 1.04;
      letter-spacing: -0.02em;
    }}
    .back-cover p {{
      margin: 0 0 0.15in;
      max-width: 4.95in;
      color: rgba(247, 241, 223, 0.82);
      font-size: 12.2px;
      line-height: 1.58;
    }}
    .back-promises {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.10in;
      max-width: 5.1in;
      margin-top: 0.26in;
    }}
    .back-promises span {{
      border-left: 0.04in solid #50d2c6;
      background: rgba(255,255,255,0.055);
      padding: 0.09in 0.12in;
      color: rgba(247, 241, 223, 0.84);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 10.2px;
      font-weight: 700;
    }}
    .back-bottom {{
      position: relative;
      z-index: 1;
      display: flex;
      justify-content: space-between;
      gap: 0.36in;
      align-items: end;
      padding-top: 0.24in;
      border-top: 1px solid rgba(247, 241, 223, 0.22);
      color: rgba(247, 241, 223, 0.72);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      font-size: 9.6px;
      line-height: 1.45;
    }}
    .back-bottom b, .back-bottom span {{
      display: block;
    }}
    .back-bottom b {{
      color: #fffaf0;
      font-size: 10.8px;
    }}
    .back-repo {{
      text-align: right;
      max-width: 2.6in;
    }}
    .section-kicker {{
      margin: 0 0 4px;
      color: var(--gold);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 9.4px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .section {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 16px 16px 14px;
      margin: 14px 0;
      box-shadow: var(--shadow);
    }}
    .no-break {{ page-break-inside: avoid; break-inside: avoid-page; }}
    .frontmatter {{ margin-top: 0; }}
    .section h2 {{
      margin: 0 0 8px;
      font-size: 21px;
      color: var(--navy);
      font-family: "Baskerville", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
    }}
    .cover h1 {{ bookmark-level: 1; }}
    .half-title {{ bookmark-level: none; }}
    .section > h2, .cluster-title {{ bookmark-level: 2; }}
    .chapter-title {{ bookmark-level: none; }}
    .case-title {{ bookmark-level: 3; }}
    .section h3 {{
      margin: 0 0 6px;
      font-size: 14px;
      color: var(--teal);
      font-family: "Baskerville", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
    }}
    .lead {{ font-size: 13px; color: var(--ink); margin: 5px 0 0; }}
    .muted {{ color: var(--muted); }}
    .tiny {{ font-size: 10px; }}
    .grid2 {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .pub-grid {{ display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 12px; }}
    .cards {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }}
    .cards.cards-wide {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(180deg, #ffffff, #f4f8fa);
      padding: 12px;
      page-break-inside: avoid;
    }}
    .card.alt {{ background: linear-gradient(180deg, #f6fbfb, #ffffff); }}
    .metric {{
      margin: 6px 0;
      font-size: 15px;
      font-weight: 800;
      color: var(--navy);
    }}
    .badge {{
      display: inline-block;
      margin: 2px 4px 2px 0;
      padding: 3px 8px;
      border-radius: 999px;
      background: #e6f2f3;
      color: #304c52;
      font-size: 10px;
      font-weight: 700;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 10.7px; margin-top: 8px; page-break-inside: auto; }}
    th, td {{ border: 1px solid #d7e3eb; padding: 7px; vertical-align: top; text-align: left; }}
    th {{ background: #eaf3f6; color: #17314b; font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif; }}
    thead {{ display: table-header-group; }}
    tfoot {{ display: table-footer-group; }}
    tr {{ page-break-inside: avoid; page-break-after: auto; }}
    .toc ol, .toc ul, ul, ol {{ margin: 6px 0 6px 18px; padding: 0; }}
    li {{ margin: 3px 0; }}
    .toc-groups {{ margin-top: 10px; }}
    .toc-group {{
      border: 1px solid #e3dccf;
      border-radius: 8px;
      background: linear-gradient(180deg, #ffffff, #f5fafb);
      padding: 10px 12px;
      margin-bottom: 8px;
      page-break-inside: avoid;
    }}
    .toc-entry {{
      display: block;
      padding: 5px 0;
      color: var(--ink);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .toc-cluster {{
      border-bottom: 1px dotted #d7cfbf;
      margin-bottom: 4px;
      font-weight: 700;
    }}
    .toc-subentries {{
      margin-left: 12px;
      padding-top: 4px;
    }}
    .toc-case {{
      font-size: 10.4px;
      color: #364754;
    }}
    .toc-entry-title {{ display: inline; }}
    .toc-count {{ color: var(--muted); font-size: 10px; margin-left: 8px; }}
    .toc-entry::after {{
      content: leader(".") target-counter(attr(href), page);
      color: var(--muted);
      float: right;
    }}
    .figure {{
      border: 1px solid #d6cebe;
      border-radius: 8px;
      background: #fbfdfe;
      padding: 8px;
      margin: 10px 0 0;
      text-align: center;
      page-break-inside: avoid;
      counter-increment: figure;
    }}
    .figure img {{ width: 100%; max-width: 860px; height: auto; border-radius: 6px; display: block; margin: 0 auto; }}
    .figure.narrow img {{ max-width: 620px; }}
    .figure.ui-shot img {{ max-width: 940px; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12); }}
    .figure.concept img {{ max-width: 900px; background: #f8fbff; }}
    .caption {{ margin: 6px 0 0; font-size: 10.2px; color: var(--muted); text-align: left; }}
    .caption::before {{
      content: "Figure " counter(figure) ". ";
      color: var(--navy);
      font-weight: 700;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .gallery {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .concept-gallery {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .figure-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(180deg, #ffffff, #f4f8fa);
      padding: 10px;
      display: grid;
      grid-template-columns: 0.95fr 1.05fr;
      gap: 10px;
      align-items: start;
      page-break-inside: avoid;
      counter-increment: figure;
    }}
    .figure-card img {{ width: 100%; height: auto; border-radius: 6px; background: #f8fbff; }}
    .concept-card {{ grid-template-columns: 1fr; }}
    .figure-card h3 {{ margin: 0 0 4px; font-size: 13px; }}
    .figure-card h3::before {{
      content: "Figure " counter(figure) ". ";
      display: block;
      margin-bottom: 4px;
      color: var(--gold);
      font-size: 9.6px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .figure-card p {{ margin: 0; font-size: 10.8px; color: var(--muted); }}
    .print-only {{ display: none; }}
    .learning-path {{
      display: grid;
      grid-template-columns: 0.82fr 1.18fr;
      gap: 12px;
      align-items: stretch;
      margin-top: 12px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: linear-gradient(180deg, #ffffff, #f4f9fb);
      padding: 12px;
      page-break-inside: avoid;
    }}
    .path-intro {{
      border-right: 1px solid #d7e3eb;
      padding-right: 12px;
    }}
    .path-intro h3 {{
      margin: 0 0 6px;
      color: var(--navy);
      font-size: 17px;
    }}
    .path-steps {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }}
    .path-step {{
      position: relative;
      border: 1px solid #d7e3eb;
      border-radius: 8px;
      background: #ffffff;
      padding: 10px 10px 10px 40px;
    }}
    .path-step span {{
      position: absolute;
      left: 10px;
      top: 10px;
      display: inline-grid;
      place-items: center;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: var(--teal);
      color: #ffffff;
      font-size: 10px;
      font-weight: 800;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .path-step h3 {{
      margin: 0 0 3px;
      font-size: 12px;
      color: var(--navy);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .path-step p {{ margin: 0; color: var(--muted); font-size: 10.4px; }}
    .cluster-head {{ display: grid; grid-template-columns: 1.3fr 0.9fr; gap: 12px; align-items: start; margin-bottom: 10px; }}
    .chapter-opener {{
      border: 1px solid var(--line);
      border-radius: 10px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.98), rgba(243, 249, 250, 0.98)),
        linear-gradient(135deg, #ffffff 0%, #edf7f8 100%);
      padding: 18px 20px 16px;
      break-before: page;
      break-after: page;
    }}
    .chapter-title {{
      margin: 0 0 8px;
      color: var(--navy);
      font-size: 28px;
      line-height: 1.12;
      font-family: "Baskerville", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
    }}
    .chapter-theme {{
      margin: 0;
      max-width: 640px;
      color: #405463;
      font-size: 13px;
    }}
    .chapter-opener-grid {{
      display: block;
      margin-top: 16px;
    }}
    .chapter-summary {{
      border: 1px solid #e2d9c9;
      border-radius: 8px;
      background: rgba(255,255,255,0.72);
      padding: 12px 14px;
    }}
    .chapter-case-strip {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }}
    .chapter-figure {{ max-width: 360px; margin-top: 12px; }}
    .chapter-figure img {{ max-width: 320px; }}
    .case-strip {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
    .case-chip {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      border: 1px solid #cbd9e2;
      background: #f3f9fb;
      color: #4b5563;
      font-size: 9.8px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .cluster {{ break-before: auto; }}
    .case {{ border-top: 2px solid #d8e4eb; padding-top: 14px; margin-top: 14px; page-break-inside: avoid; }}
    .case:first-of-type {{ border-top: none; padding-top: 0; margin-top: 0; }}
    .case-head {{ display: grid; grid-template-columns: 1.25fr 0.95fr; gap: 12px; align-items: start; }}
    .case-title {{
      margin-top: 0;
      padding-bottom: 5px;
      border-bottom: 1px solid #d7e3eb;
    }}
    .case-meta {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; font-size: 10.4px; }}
    .case-meta > div {{ border: 1px solid var(--line); border-radius: 8px; padding: 8px; background: var(--panel); }}
    .case-meta b {{ display: block; color: var(--muted); margin-bottom: 4px; font-size: 9.8px; text-transform: uppercase; letter-spacing: 0.06em; font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif; }}
    .case-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 10px; }}
    .narrative h4 {{ margin: 0 0 4px; font-size: 12px; color: var(--navy); }}
    .study-note, .stepbox, .resultbox, .expected, .interpret, .biology,
    .glossary-strip, .evidence-box, .decision-card, .mistake-box, .chief-box, .cluster-checkpoint {{
      margin-top: 10px;
      border-radius: 8px;
      padding: 10px 12px;
      page-break-inside: avoid;
    }}
    .study-note {{ border: 1px solid #d6c08d; border-left: 4px solid var(--gold); background: #fffaf0; }}
    .stepbox {{ border: 1px solid #bcd8dd; border-left: 4px solid var(--teal); background: #f3fafb; }}
    .resultbox {{ border: 1px solid #cbd9e2; border-left: 4px solid var(--navy); background: #f7fafc; }}
    .expected {{ border: 1px solid #c8dfcf; border-left: 4px solid #4f8a5b; background: #f6fbf7; }}
    .interpret {{ border: 1px solid #e4d7ab; border-left: 4px solid var(--gold); background: #fff9eb; }}
    .biology {{ border: 1px solid #e1cbd6; border-left: 4px solid var(--rose); background: #fdf6f9; }}
    .glossary-strip {{ border: 1px solid #cbd9e2; border-left: 4px solid #446d9b; background: #f5f8fc; }}
    .evidence-box {{ border: 1px solid #bdd7d8; border-left: 4px solid var(--teal); background: #f1faf9; }}
    .decision-card {{ border: 1px solid #c8dfcf; border-left: 4px solid #4f8a5b; background: #f5fbf6; }}
    .mistake-box {{ border: 1px solid #e7c1bf; border-left: 4px solid #b7504c; background: #fff7f5; }}
    .chief-box {{ border: 1px solid #ddd0e2; border-left: 4px solid var(--rose); background: #fbf6fd; }}
    .cluster-checkpoint {{ border: 1px solid #d7e3eb; border-left: 4px solid var(--navy); background: #f6f9fb; margin-bottom: 10px; }}
    .study-note b, .stepbox b, .resultbox b, .expected b, .interpret b, .biology b,
    .glossary-strip > b, .evidence-box > b, .decision-card > b, .mistake-box > b, .chief-box > b, .cluster-checkpoint > b {{
      display: block;
      margin-bottom: 4px;
      color: var(--navy);
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .glossary-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 7px; }}
    .glossary-card {{ border: 1px solid #d7e3eb; border-radius: 7px; background: #ffffff; padding: 8px; }}
    .glossary-card h4 {{ margin: 0 0 3px; color: var(--teal); font-size: 11.2px; }}
    .glossary-card p {{ margin: 2px 0; font-size: 10.2px; line-height: 1.45; }}
    .evidence-grid, .checkpoint-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .checkpoint-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .evidence-grid h4, .checkpoint-grid h4 {{ margin: 2px 0 4px; color: var(--teal); font-size: 11.5px; }}
    .decision-card p, .mistake-box p {{ margin: 3px 0; }}
    .decision-card span, .mistake-box span {{ color: var(--navy); font-weight: 800; font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif; }}
    .chief-box ul, .evidence-box ul, .cluster-checkpoint ul {{ margin-bottom: 0; }}
    .cheat-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; }}
    .cheat-card {{ border: 1px solid var(--line); border-top: 4px solid var(--teal); border-radius: 8px; background: #ffffff; padding: 10px; page-break-inside: avoid; }}
    .cheat-card h3 {{ color: var(--navy); font-size: 12px; margin-bottom: 5px; }}
    .cheat-card p {{ margin: 4px 0; font-size: 10.2px; }}
    h2, h3, h4 {{ break-after: avoid-page; page-break-after: avoid; }}
    .card, .figure {{ break-inside: avoid-page; page-break-inside: avoid; }}
    @media print {{
      body {{
        background: #ffffff;
        font-size: 10.9px;
        line-height: 1.58;
      }}
      .doc {{
        max-width: none;
        margin: 0;
        padding: 0;
      }}
      .section, .cover, .card, .figure, .figure-card, .cover-shot, .imprint-box {{
        box-shadow: none;
      }}
      .section {{
        break-before: page;
        break-inside: auto;
        page-break-inside: auto;
        margin: 0 0 7mm;
        padding: 0;
        border: 0;
        border-radius: 0;
        background: transparent;
      }}
      .section.no-break {{
        break-before: page;
        break-inside: avoid-page;
        page-break-inside: avoid;
      }}
      .section > h2 {{
        padding-bottom: 2.5mm;
        border-bottom: 0.35mm solid #d7e3eb;
        margin-bottom: 4mm;
      }}
      .section-kicker {{
        margin-top: 0;
        break-after: avoid-page;
        page-break-after: avoid;
      }}
      .frontmatter {{
        break-before: page;
      }}
      .grid2, .pub-grid, .cards, .cards.cards-wide {{
        display: block;
      }}
      .grid2 > *, .pub-grid > *, .cards > * {{
        margin-bottom: 4mm;
      }}
      .card, .toc-group, .learning-path, .path-step, .figure-card {{
        border-radius: 0;
        background: #ffffff;
      }}
      .card {{
        padding: 4mm;
      }}
      .learning-path {{
        display: block;
        margin-top: 4mm;
        padding: 4mm;
      }}
      .path-intro {{
        border-right: 0;
        border-bottom: 1px solid #d7e3eb;
        padding-right: 0;
        padding-bottom: 3mm;
        margin-bottom: 3mm;
      }}
      .path-steps {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 3mm;
      }}
      .figure {{
        margin: 5mm 0 4mm;
        padding: 3mm;
        border-radius: 0;
        break-inside: avoid-page;
      }}
      .figure img {{
        max-width: 100%;
        max-height: 150mm;
        object-fit: contain;
      }}
      .figure.ui-shot img {{
        max-height: 132mm;
        box-shadow: none;
      }}
      .figure.concept img {{
        max-height: 140mm;
      }}
      .gallery, .concept-gallery {{
        display: block;
      }}
      .figure-card {{
        display: block;
        margin-bottom: 6mm;
        padding: 4mm;
      }}
      .figure-card img {{
        max-height: 132mm;
        object-fit: contain;
      }}
      .print-only {{ display: block; }}
      .cluster-head {{ display: none; }}
      .cluster {{
        break-before: right;
        margin: 0;
        padding: 0;
      }}
      .chapter-opener {{
        min-height: 8.95in;
        display: flex;
        flex-direction: column;
        justify-content: center;
        break-before: right;
        break-after: page;
        border: 0;
        border-radius: 0;
        background: transparent;
        padding: 0;
      }}
      .chapter-title {{
        max-width: 150mm;
        font-size: 31px;
      }}
      .chapter-theme {{
        max-width: 142mm;
        font-size: 13.5px;
      }}
      .chapter-summary {{
        margin-top: 8mm;
        border-radius: 0;
        background: #ffffff;
      }}
      .chapter-figure {{
        max-width: 118mm;
        margin-top: 8mm;
      }}
      .chapter-figure img {{
        max-height: 76mm;
        object-fit: contain;
      }}
      .case {{
        break-before: page;
        break-inside: auto;
        page-break-inside: auto;
        margin: 0;
        padding-top: 0;
        border-top: 0;
      }}
      .case-head {{
        display: block;
        break-inside: avoid-page;
        padding-bottom: 3mm;
        margin-bottom: 4mm;
        border-bottom: 0.4mm solid #d8e4eb;
      }}
      .case-title {{
        border-bottom: 0;
        margin-bottom: 2mm;
        padding-bottom: 0;
        font-size: 18px;
      }}
      .case-meta {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 3mm;
        margin-top: 4mm;
        break-inside: avoid-page;
      }}
      .case-meta > div {{
        border-radius: 0;
        padding: 2.6mm;
      }}
      .case-grid {{
        display: block;
        margin-top: 0;
      }}
      .case-grid .card {{
        break-inside: auto;
        page-break-inside: auto;
        margin-bottom: 4mm;
      }}
      .study-note, .stepbox, .expected, .interpret, .biology,
      .glossary-strip, .evidence-box, .decision-card, .mistake-box, .chief-box, .cluster-checkpoint {{
        break-inside: avoid-page;
        page-break-inside: avoid;
      }}
      .resultbox {{
        break-inside: auto;
        page-break-inside: auto;
      }}
      .study-note, .stepbox, .resultbox, .expected, .interpret, .biology,
      .glossary-strip, .evidence-box, .decision-card, .mistake-box, .chief-box, .cluster-checkpoint {{
        border-radius: 0;
        margin-top: 4mm;
        padding: 3.2mm 3.8mm;
      }}
      .glossary-grid, .evidence-grid, .checkpoint-grid, .cheat-grid {{
        display: block;
      }}
      .glossary-card, .cheat-card {{
        border-radius: 0;
        margin-bottom: 3mm;
      }}
      pre {{
        break-inside: auto;
        page-break-inside: auto;
        font-size: 9.1px;
        line-height: 1.36;
      }}
      table {{
        font-size: 9.7px;
      }}
      th, td {{
        padding: 2.4mm;
      }}
    }}
    @media screen {{
      .print-only {{ display: none !important; }}
    }}
  </style>
</head>
<body>
  <main class="doc">
    {render_front_cover(case_count)}

    {render_inside_front_cover(case_count)}

    {render_half_title_page()}

    {render_imprint_page(case_count)}

    {render_publication_note(case_count)}

    <section class="section no-break">
      <p class="section-kicker">Course Map</p>
      <h2>Learning Path</h2>
      <p class="muted">The tutorial is organized as a reasoning sequence: identify the biological object, design the experiment, evaluate the evidence, then package the work so another person can trust it.</p>
      {render_learning_path(case_count)}
    </section>

    <section class="section no-break">
      <p class="section-kicker">Using This Edition</p>
      <h2>How to Use This Edition</h2>
      <div class="grid2">
        <div class="card">
          <h3>Quickstart</h3>
          <p>1. Start the web UI with <code>python3 web_ui.py --port 8080</code>.</p>
          <p>2. Materialize a case bundle with <code>{escape(case_bundle_command('A'))}</code>.</p>
          <p>3. Open <code>http://127.0.0.1:8080</code>, load the FASTA from your case bundle, and follow the matching case steps below.</p>
        </div>
        <div class="card alt">
          <h3>What This Edition Adds</h3>
          <p>This edition explains what the input data are, why the task matters biologically, what a meaningful result looks like, and what you should not conclude from the output.</p>
          <p>It is built so the numbers point to a real scientific story, and the ambiguity-aware methods are taught directly rather than left implicit.</p>
        </div>
      </div>
    </section>

    <section class="section">
      <p class="section-kicker">Orientation</p>
      <h2>Meaningful Results Preview</h2>
      <p class="muted">These quick facts are derived directly from the bundled records and serve as a calibration point before you begin the {case_count} lessons.</p>
      {render_featured_results()}
    </section>

    <section class="section">
      <p class="section-kicker">Data</p>
      <h2>How to Use the Sample Data</h2>
      <div class="grid2">
        <div class="card">
          <h3>Bundled Data Files</h3>
          <ul>
            <li><code>docs/tutorial/datasets/training_real_world_sequences.fasta</code>: base public-source sequences.</li>
            <li><code>docs/tutorial/datasets/training_real_world_dataset.json</code>: metadata, sources, case inputs, and derived-record definitions.</li>
            <li><code>docs/tutorial/datasets/case_playbook.md</code>: compact case-by-case checklist.</li>
            <li><code>docs/tutorial/datasets/case_bundles/</code>: prebuilt ready-to-load bundles for all {case_count} tutorial cases.</li>
            <li><code>docs/tutorial/datasets/extract_case_bundle.py</code>: writes ready-to-run per-case FASTA bundles.</li>
          </ul>
        </div>
        <div class="card alt">
          <h3>One Good Workflow Habit</h3>
          <p>Always save the exact case bundle you used. That keeps the tutorial reproducible and avoids “I think I loaded the right sequence” problems. Every case already ships with a prebuilt bundle, so you can start quickly and still regenerate it later if you want to inspect provenance.</p>
          <pre>{escape(case_bundle_command('K'))}</pre>
        </div>
      </div>
    </section>

    <section class="section">
      <p class="section-kicker">Study Method</p>
      <h2>How to Study This Book</h2>
      <div class="cards">
        <div class="card">
          <h3>Read the data type first</h3>
          <p>Before you run anything, identify whether the input is a coding sequence, genomic fragment, plasmid-like construct, chromatogram-derived consensus, or uncertainty-bearing record. Most downstream mistakes come from treating those as interchangeable.</p>
        </div>
        <div class="card">
          <h3>Use the sample results as calibration, not as a cheat sheet</h3>
          <p>The sample results tell you what a believable answer should feel like. They do not replace your own run. A good habit is to compare your output to the sample and ask why any difference exists.</p>
        </div>
        <div class="card">
          <h3>Write down the biological claim separately from the software output</h3>
          <p>The result is not just “the tool said X.” The result is the biological sentence you can defend after seeing X. That distinction is what turns software use into bioinformatics reasoning.</p>
        </div>
      </div>
    </section>

    <section class="section">
      <p class="section-kicker">Reasoning Loop</p>
      <h2>Evidence-to-Decision Framework</h2>
      <p class="muted">Every workflow in this book should end with a decision, not merely a screenshot. Genome Forge now teaches the same compact loop in the tutorial and in the web UI: observe evidence, state the inference, name the confidence limit, and choose the next bench or review action.</p>
      <div class="cards">
        <div class="card"><h3>Evidence</h3><p>What did the software actually observe or compute: a cut count, a trace peak, a primer product, a sequence alignment, or a saved history state?</p></div>
        <div class="card"><h3>Inference</h3><p>What biological claim does that evidence support, and what assumption connects the output to the claim?</p></div>
        <div class="card"><h3>Decision</h3><p>What should happen next at the bench or in review: proceed, repeat, reject, redesign, document, or seek more evidence?</p></div>
      </div>
    </section>

    <section class="section">
      <p class="section-kicker">CS-to-Biology Bridge</p>
      <h2>Glossary for Computer Scientists</h2>
      <p class="muted">Use this table as the translation layer between sequence-as-string intuition and DNA-as-physical-molecule reasoning. The same terms also appear as just-in-time glossary cards inside the cases where they matter most.</p>
      {render_global_glossary()}
    </section>

    <section class="section">
      <p class="section-kicker">Printable Reference</p>
      <h2>One-Page Cheat Sheets for Core Evidence Types</h2>
      <p class="muted">These cards are meant for double-sided printing or quick lab-bench review. Each one tells you what to read, when to use it, and the beginner mistake to avoid.</p>
      {render_cheat_sheets()}
    </section>

    <section class="section">
      <p class="section-kicker">Reference</p>
      <h2>Primer on Ambiguity Codes</h2>
      <p class="muted">Several later lessons teach ambiguity-aware matching directly. These symbols do not mean the sequence is broken. They mean the evidence still permits a small set of bases at a position, and Genome Forge can search, compare, and design around that uncertainty.</p>
      {render_iupac_table()}
      <div class="cards" style="margin-top:10px">
        <div class="card"><h3>Why ambiguity is honest</h3><p>Forcing an uncertain position to one exact base may look cleaner, but it destroys evidence. Ambiguity codes preserve what the data still allow.</p></div>
        <div class="card"><h3>Why assay design cares</h3><p>Degenerate primers use these symbols on purpose so one assay can still cover a small family of related templates.</p></div>
        <div class="card"><h3>Why search still works</h3><p>An uncertainty-bearing query can still identify the correct molecule family if the unresolved positions are represented explicitly instead of hidden.</p></div>
      </div>
    </section>

    <section class="section">
      <p class="section-kicker">Interface</p>
      <h2>Visual Tour of the Workbench</h2>
      <p class="muted">These illustrations help you recognize what Genome Forge is showing in each workflow: structure, evidence, divergence, and provenance.</p>
      {render_visual_gallery()}
    </section>

    <section class="section">
      <p class="section-kicker">Biology Background</p>
      <h2>Three Concepts That Deserve Pictures</h2>
      <p class="muted">A review of the expanded tutorial found three places where a reader with limited biology background benefits from an explanatory illustration before touching the software: diagnostic digest logic, silent restriction-site design, and Sanger trace evidence review.</p>
      {render_concept_gallery()}
    </section>

    <section class="section">
      <p class="section-kicker">Biological Objects</p>
      <h2>Real-World Record Field Guide</h2>
      <p>These are the biological objects that power the tutorial. Some are public-source sequences bundled directly in the FASTA file. Others are clearly labelled training derivatives created so specific comparison cases have an answer key.</p>
      <table>
        <thead><tr><th>Record</th><th>Origin</th><th>Why it matters</th><th>Input data explained</th><th>Source</th></tr></thead>
        <tbody>{record_reference_table()}</tbody>
      </table>
      <div class="cards" style="margin-top:10px">
        <div class="card"><h3>Reporter Biology</h3><p>EGFP and mCherry let you practice coding-sequence analysis on records that many labs actually clone, image, and verify.</p></div>
        <div class="card"><h3>Cloning Architecture</h3><p>pUC19 MCS and lacZ alpha turn restriction logic into an experimentally meaningful story because the vector design is tied to blue-white screening.</p></div>
        <div class="card"><h3>Disease-Linked DNA</h3><p>The BRAF fragment keeps the course grounded in medically important sequence interpretation, not only reporter-gene demos.</p></div>
      </div>
    </section>

    <section class="section toc" role="doc-toc" aria-label="Table of contents">
      <p class="section-kicker">Contents</p>
      <h2>Table of Contents</h2>
      <p class="muted">Recommended order for readers new to biology: Cluster A → B → C → D → G → E → F → H.</p>
      {toc_html}
    </section>

    <section class="section">
      <p class="section-kicker">Interpretation</p>
      <h2>How to Read a Bioinformatics Result Like a Scientist</h2>
      <div class="cards">
        <div class="card"><h3>Start with the biological question</h3><p>Ask what decision the output is supposed to support. A beautiful visualization is not useful if it does not change a real experimental choice.</p></div>
        <div class="card"><h3>Respect the input data type</h3><p>A genomic fragment, a coding sequence, a plasmid map, and a chromatogram are not interchangeable. The same algorithm can be correct and still be answering the wrong question.</p></div>
        <div class="card"><h3>Separate observation from inference</h3><p>Report what the tool measured first, then explain what you think that measurement means biologically, and finally say how confident you are.</p></div>
      </div>
    </section>

    {cluster_sections}

    {render_back_cover(case_count)}
  </main>
</body>
</html>
''')


def build_case_inputs() -> list[dict]:
    rows = []
    for case_info in CASES:
        guide = guide_for_case(case_info)
        profile = decision_profile(case_info)
        rows.append({
            'case_id': case_info['id'],
            'title': case_info['title'],
            'cluster': case_info['cluster'],
            'records': case_info['records'],
            'tab': case_info['tab'],
            'workflow': case_info['workflow'],
            'apis': case_info['apis'],
            'ui_walkthrough': {
                'tab': guide['tab'],
                'button': guide['button'],
                'panel': guide['panel'],
                'fields': guide['fields'],
            },
            'decision_card': profile,
            'glossary_terms': glossary_terms_for_case(case_info),
            'extract_command': case_bundle_command(case_info['id']),
            'prebuilt_bundle_dir': f'docs/tutorial/datasets/case_bundles/case_{case_info["id"].lower()}',
        })
    return rows


def build_dataset_json() -> dict:
    return {
        'dataset_name': 'genomeforge_training_real_world_v2',
        'created_at': TODAY,
        'overview': 'Real-world teaching bundle for the Genome Forge tutorial, including public-source records and clearly labeled training derivatives.',
        'usage_tips': [
            'Use extract_case_bundle.py to materialize the exact records for one case.',
            'Base public-source sequences live in training_real_world_sequences.fasta.',
            'Derived training records are generated from public-source parents using explicit edit lists stored in this JSON.',
        ],
        'record_sets': RECORD_SETS,
        'records': [
            {'name': name, **info}
            for name, info in RECORDS.items()
        ],
        'case_inputs': build_case_inputs(),
        'enzyme_panels': {
            'mapping_panel': ['EcoRI', 'BamHI', 'HindIII', 'XbaI', 'PstI', 'KpnI'],
            'ligation_panel': {
                'vector_left_enzyme': 'EcoRI',
                'vector_right_enzyme': 'BamHI',
                'insert_left_enzyme': 'BamHI',
                'insert_right_enzyme': 'EcoRI',
            },
        },
        'primer_training': {
            'primary_target': 'BRAF_exon15_fragment',
            'background_records': ['EGFP_CDS', 'mCherry_CDS', 'BRAF_exon15_fragment'],
            'default_window': {'target_start': 40, 'target_end': 170, 'window_bp': 140},
        },
        'crispr_training': {
            'primary_target': 'BRAF_exon15_fragment',
            'pam': 'NGG',
            'spacer_len': 20,
            'hdr_example': {
                'edit_start_1based': 97,
                'edit_end_1based': 99,
                'edit_sequence': 'GAG',
                'left_arm_bp': 60,
                'right_arm_bp': 60,
            },
        },
        'collaboration_training': {
            'workspace_name': 'lab_workspace_training',
            'owner': 'owner_user',
            'editor': 'editor_user',
            'reviewer': 'reviewer_user',
        },
    }


def render_playbook() -> str:
    cluster_titles = {cluster['id']: cluster['title'] for cluster in CLUSTERS}
    lines = [
        '# Genome Forge Training Case Playbook',
        '',
        'This playbook mirrors the tutorial exactly. Use it as the fast checklist after you have read the full narrative in the HTML/PDF version.',
        '',
    ]
    for cluster in CLUSTERS:
        lines.extend([f'## Cluster {cluster["id"]}: {cluster["title"]}', ''])
        for case_info in CLUSTER_CASES[cluster['id']]:
            profile = decision_profile(case_info)
            guide = guide_for_case(case_info)
            lines.extend([
                f'## Case {case_info["id"]}: {case_info["title"]}',
                '',
                f'- Cluster: {cluster_titles[case_info["cluster"]]}',
                f'- Focus: {case_info["biological_question"]}',
                f'- Records: {", ".join(case_info["records"])}',
                f'- Workflow: {case_info["workflow"]}',
                f'- UI path: {guide["tab"]} tab -> `{guide["button"]}` -> {guide["panel"]}',
                f'- APIs: {", ".join(case_info["apis"])}',
                f'- Extract bundle: `{case_bundle_command(case_info["id"])} `'.rstrip(),
                f'- Key expected signal: {case_info["expected"][0]}',
                f'- Evidence/inference checkpoint: {case_info["interpretation"][0]}',
                f'- Bench decision: {profile["decision"]}',
                f'- Common caution: {profile["caution"]}',
                '',
            ])
    return '\n'.join(lines).rstrip() + '\n'


def render_dataset_readme() -> str:
    return dedent(f'''
    # Genome Forge Tutorial Datasets

    This folder contains the reproducible sample data used by the self-study tutorial.

    ## Files

    - `training_real_world_sequences.fasta`: public-source base records bundled directly in FASTA.
    - `training_real_world_dataset.json`: metadata, sources, case-to-record mapping, and definitions for derived training records.
    - `case_playbook.md`: compact tutorial checklist.
    - `case_bundles/`: prebuilt ready-to-load bundles for all {len(CASES)} cases.
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
    ''').strip() + '\n'


def write_case_bundle(case_info: dict, base_sequences: dict[str, str]) -> None:
    out_dir = CASE_BUNDLES_DIR / f'case_{case_info["id"].lower()}'
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_records = []
    fasta_lines = []
    for record_name in case_info['records']:
        info = RECORDS[record_name]
        seq = resolved_record_sequence(record_name, base_sequences)
        fasta_lines.append(f'>{record_name}')
        fasta_lines.append(seq)
        (out_dir / f'{record_name}.fasta').write_text(f'>{record_name}\n{seq}\n', encoding='utf-8')
        manifest_records.append(
            {
                'name': record_name,
                'type': info.get('type', 'unknown'),
                'topology': info.get('topology', 'linear'),
                'origin': info.get('origin', ''),
                'why_it_matters': info.get('why_it_matters', ''),
                'source_label': info.get('source_label', ''),
                'source_url': info.get('source_url', ''),
            }
        )
    (out_dir / 'records.fasta').write_text('\n'.join(fasta_lines) + '\n', encoding='utf-8')
    manifest = {
        'case': {
            'case_id': case_info['id'],
            'title': case_info['title'],
            'cluster': case_info['cluster'],
            'tab': case_info['tab'],
            'workflow': case_info['workflow'],
            'apis': case_info['apis'],
        },
        'records': manifest_records,
    }
    (out_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


def write_all_case_bundles() -> None:
    base_sequences = load_fasta_records()
    CASE_BUNDLES_DIR.mkdir(parents=True, exist_ok=True)
    for case_info in CASES:
        write_case_bundle(case_info, base_sequences)


def main() -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(render_html(), encoding='utf-8')
    PLAYBOOK_PATH.write_text(render_playbook(), encoding='utf-8')
    DATASET_JSON_PATH.write_text(json.dumps(build_dataset_json(), indent=2), encoding='utf-8')
    DATASET_README_PATH.write_text(render_dataset_readme(), encoding='utf-8')
    write_all_case_bundles()
    print(f'Wrote {HTML_PATH}')
    print(f'Wrote {PLAYBOOK_PATH}')
    print(f'Wrote {DATASET_JSON_PATH}')
    print(f'Wrote {DATASET_README_PATH}')
    print(f'Wrote {CASE_BUNDLES_DIR}')


if __name__ == '__main__':
    main()
