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
    case('Z', 'Multi-Trace Consensus for Final Construct Call', 'D', ['EGFP_CDS'], 'Trace', 'Combine multiple trace-derived views into one final verdict about a reporter construct.', ['/api/import-ab1', '/api/trace-align', '/api/trace-consensus'],
         'When several sequencing reads exist for the same construct, how do you combine them into one decision rather than trusting the loudest trace?',
         'This case uses a real reporter CDS because plasmid verification is one of the most common reasons a lab reaches for sequence traces. The record is familiar, which keeps the attention on evidence integration rather than reference confusion.',
         'Consensus building is an evidence aggregation problem. A single noisy trace can be misleading; several partially overlapping traces can support a stable call. The skill is deciding when disagreement reflects noise, chemistry, or a real sequence change.',
         'Consensus is not democracy; three low-quality reads do not magically beat one high-quality read. Quality still matters.',
         {'trace_count': 3, 'consensus_mismatches_vs_reference': 0, 'final_verdict': 'construct confirmed'},
         ['A multi-trace summary with overlap or mismatch hotspots identified explicitly.', 'A consensus sequence or final mismatch count relative to the expected construct.', 'A final verification verdict with confidence language.'],
         ['Agreement across independent traces raises confidence, especially when the same region is supported more than once.', 'Disagreement near weak peaks should be treated differently from disagreement in high-quality regions.', 'Your final call should always say whether the evidence is enough to proceed.'],
         'changing the trace subset or quality threshold'),
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
    case('R', 'Promoter/RBS Context for Expression Tuning', 'F', ['lacZ_alpha_fragment', 'EGFP_CDS'], 'Advanced', 'Use annotation and translation context to discuss why expression output depends on more than the CDS alone.', ['/api/auto-annotate', '/api/sequence-tracks'],
         'Why can two constructs with the same coding sequence express differently in cells or bacteria?',
         'This case intentionally uses a familiar reporter CDS plus a vector-associated expression context discussion. The tutorial point is conceptual: CDS correctness is necessary, but expression strength is influenced by promoter and translation-initiation context as well.',
         'Engineers often start with the code analogy that the CDS is the “program.” In biology, the promoter and ribosome-binding context are closer to the runtime environment and scheduler. The same code can behave very differently when the surrounding control logic changes.',
         'A perfect CDS in the wrong context is like efficient code behind a broken API gateway: nothing useful reaches the user.',
         {'dominant_takeaway': 'regulatory context can dominate phenotype', 'reporter_cds_intact': True, 'status': 'interpret expression with regulatory context in mind'},
         ['A diagram or explanation that separates coding sequence from regulatory context.', 'A specific note on how promoter or translation-initiation context could alter outcome.', 'A warning against equating “correct CDS” with “correct phenotype.”'],
         ['When phenotype and sequence disagree, regulation is one of the first places to look.', 'This is a conceptual case: the value is in learning what extra information you would seek next.', 'Always separate “what is encoded” from “how strongly and when it is used.”'],
         'changing the annotated feature context'),
    case('V', 'Codon Usage Bias and Host Portability', 'F', ['EGFP_CDS', 'mCherry_CDS'], 'Advanced', 'Discuss how two common reporter CDS records might look to different host translation systems.', ['/api/codon-optimize'],
         'If you move a gene between hosts, what sequence properties might become limiting even when the protein target stays the same?',
         'Reporter genes are excellent portability examples because labs routinely move them among bacteria, mammalian cells, and synthetic constructs. The DNA sequence is portable, but the translation machinery and expression context are not identical across hosts.',
         'Codon bias is a reminder that biology has multiple layers of compatibility. The amino-acid sequence may be the same after translation, yet the nucleotide-level implementation can influence expression efficiency, stability, and synthesis convenience in a particular host.',
         'Codon optimization is like changing the accent of a sentence without changing its literal meaning: the content stays similar, but the local audience may understand it far more easily.',
         {'host_comparison': ['E. coli-like', 'mammalian-like'], 'optimization_goal': 'retain protein while changing codon preferences', 'interpretation': 'sequence portability is host-dependent'},
         ['A codon-optimization or codon-bias summary tied to a specific host scenario.', 'A statement about what changed at the nucleotide level and what stayed constant at the protein level.', 'A caution that codon optimization does not solve every expression problem.'],
         ['Codon changes can improve expression without changing the amino-acid sequence, but they can also affect RNA behavior and other features.', 'A portable tutorial answer distinguishes protein identity from nucleotide implementation.', 'Optimization should be justified by a host-specific problem, not used as a reflex.'],
         'changing the target host preference'),
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
    case('AJ', 'BLAST-like Similarity Search for Identity, Origin, and Contamination', 'G', ['EGFP_CDS', 'mCherry_CDS', 'lacZ_alpha_fragment', 'BRAF_exon15_fragment'], 'Advanced', 'Run local similarity search against a small real-world panel to identify the most likely source of an unknown sequence.', ['/api/blast-search'],
         'If someone hands you a mystery sequence, which known molecule in your local panel does it most resemble?',
         'The training panel mixes reporter genes, a vector-linked fragment, and a human genomic fragment. That is exactly the kind of mixed local reference set a real lab accumulates over time, which makes the search results practically useful.',
         'Similarity search is not just about identity percentages. Coverage, ranking, and context all matter. A high-identity partial hit can mean something very different from a full-length match, especially when you are trying to infer sample origin or contamination.',
         'BLAST-like search is one of the fastest ways to turn a mystery sequence into a shortlist of plausible stories.',
         {'top_hit': 'EGFP_CDS', 'identity_pct': 100.0, 'query_coverage_pct': 100.0, 'runner_up': 'mCherry_CDS'},
         ['A ranked hit list with identity and coverage, not just a single best match.', 'A narrative about what the top hit implies for sample identity or origin.', 'A note explaining whether the hit pattern suggests clean identity or mixed origin.'],
         ['Full-length high-identity hits support strong identity claims.', 'Partial hits are clues, not final answers; always inspect coverage.', 'The runner-up hits often help explain contamination or domain sharing.'],
         'changing the query sequence or database panel'),
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


def render_record_badges(records: list[str]) -> str:
    return ''.join(f'<span class="badge">{escape(record)}</span>' for record in records)


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


def render_publication_note(case_count: int) -> str:
    return dedent(f'''
      <section class="section frontmatter">
        <p class="section-kicker">Front Matter</p>
        <h2>Publication Notes</h2>
        <div class="pub-grid">
          <div class="card">
            <h3>Abstract</h3>
            <p>This tutorial is designed as a publication-style course reader for learning practical bioinformatics with Genome Forge. It combines real biological records, stepwise software workflows, expected outputs, interpretation guidance, and biological explanation in one reproducible volume.</p>
            <p>The current edition contains {case_count} lessons arranged into themed clusters that progress from molecular architecture and restriction logic through assay design, assembly, comparative reasoning, ambiguity-aware analysis, and reproducible project delivery.</p>
          </div>
          <div class="card alt">
            <h3>Edition and Citation</h3>
            <p><b>Edition:</b> Genome Forge Textbook Edition, generated from repository source on <code>{escape(TODAY)}</code>.</p>
            <p><b>Preferred citation:</b> <i>Teach Yourself Bioinformatics with Genome Forge</i>, Genome Forge {escape(APP_VERSION)}, tutorial edition.</p>
            <p><b>Formats:</b> HTML and PDF are generated from the same source, so case numbering, sample data, and screenshots stay aligned.</p>
          </div>
        </div>
      </section>
    ''').strip()


def render_half_title_page() -> str:
    return dedent(f'''
      <section class="half-title-page" aria-label="Half title page">
        <p class="half-title-kicker">Genome Forge Tutorial</p>
        <h1 class="half-title">Teach Yourself Bioinformatics with Genome Forge</h1>
        <p class="half-subtitle">Textbook Edition · Real-world records · Publication-style self-study guide</p>
      </section>
    ''').strip()


def render_imprint_page(case_count: int) -> str:
    return dedent(f'''
      <section class="imprint-page" aria-label="Imprint page">
        <div class="imprint-box">
          <p class="section-kicker">Imprint</p>
          <h2 class="imprint-title">Edition and Copyright</h2>
          <p><b>Title:</b> <i>Teach Yourself Bioinformatics with Genome Forge</i></p>
          <p><b>Edition:</b> Genome Forge {escape(APP_VERSION)} textbook edition generated on <code>{escape(TODAY)}</code>.</p>
          <p><b>Authoring body:</b> {escape(TUTORIAL_AUTHOR)}</p>
          <p><b>Repository:</b> <a href="{escape(REPO_URL)}">{escape(REPO_URL)}</a></p>
          <p><b>License:</b> Apache License 2.0 for the project source; public-source records and clearly labelled training derivatives are documented in the bundled dataset metadata.</p>
          <p><b>Scope:</b> This volume contains {case_count} lessons, real-world sample data, and generated HTML/PDF outputs that are rebuilt from the same source-of-truth tutorial generator.</p>
          <p><b>Suggested citation:</b> {escape(TUTORIAL_AUTHOR)}. <i>Teach Yourself Bioinformatics with Genome Forge</i>. Genome Forge {escape(APP_VERSION)}. {escape(COPYRIGHT_YEAR)}.</p>
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


def render_case(case_info: dict) -> str:
    records = case_info['records']
    record_details = ' '.join(RECORDS[name]['input_details'] for name in records)
    starter_values = case_info.get('starter_values', [])
    steps = [
        f'Use the included prebuilt bundle <code>{escape(prebuilt_case_bundle_path(case_info["id"]))}</code> or regenerate it with <code>{escape(case_bundle_command(case_info["id"]))}</code>.',
        f"Open the <code>{escape(case_info['tab'])}</code> tab in Genome Forge and load: <code>{escape(', '.join(records))}</code>.",
        f"Run <code>{escape(case_info['workflow'])}</code> once with default settings, then rerun after {escape(case_info['parameter_knob'])}.",
        'Capture one screenshot of the main result panel so you can compare your run with the sample interpretation later.',
        f"Record the relevant endpoint(s): <code>{escape(', '.join(case_info['apis']))}</code> and write one sentence explaining the biological takeaway.",
    ]
    expected = case_info['expected']
    interpretation = case_info['interpretation']
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
        <div class="stepbox"><b>Step-by-Step in Genome Forge</b><ol>{format_list(steps, escape_items=False)}</ol></div>
        {screenshot_html}
        <div class="resultbox"><b>Sample Results</b><p class="muted">Representative output shaped around the bundled real-world record(s) or their documented training derivatives. Values are rounded for readability, but the biological story is tied to the included data.</p><pre>{format_json_block(case_info['sample_result'])}</pre></div>
        <div class="expected"><b>Expected Results</b><ul>{format_list(expected)}</ul></div>
        <div class="interpret"><b>How to Interpret the Results</b><ul>{format_list(interpretation)}</ul></div>
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
              <h3>Included Lessons</h3>
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
  <meta name="description" content="Publication-style self-study bioinformatics tutorial for Genome Forge using real biological records, stepwise workflows, and biological interpretation." />
  <meta name="keywords" content="bioinformatics, DNA, cloning, plasmid, genome forge, tutorial, molecular biology" />
  <meta name="generator" content="Genome Forge tutorial generator" />
  <meta name="dcterms.created" content="{escape(TODAY)}" />
  <meta name="dcterms.modified" content="{escape(TODAY)}" />
  <title>Teach Yourself Bioinformatics with Genome Forge ({escape(APP_VERSION)})</title>
  <style>
    @page {{
      size: A4;
      margin: 17mm 15mm 20mm 15mm;
    }}
    @page :left {{
      margin-left: 18mm;
      margin-right: 14mm;
      @top-left {{
        content: "Teach Yourself Bioinformatics with Genome Forge";
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
      margin-left: 14mm;
      margin-right: 18mm;
      @top-right {{
        content: "Genome Forge Tutorial";
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
      --ink: #1d2733;
      --muted: #5c6773;
      --line: #d8d3c9;
      --panel: #fbf8f1;
      --panel-strong: #f3ede1;
      --navy: #24364b;
      --teal: #335e63;
      --gold: #9e6a2e;
      --rose: #7d4f5d;
      --paper: #fffdf8;
      --shadow: 0 12px 34px rgba(52, 55, 57, 0.08);
      --code-bg: #0b1220;
      --code-ink: #dbeafe;
    }}
    * {{ box-sizing: border-box; }}
    html {{ hyphens: auto; }}
    body {{
      margin: 0;
      background: #f4efe6;
      color: var(--ink);
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
      font-size: 11.3px;
      line-height: 1.64;
      counter-reset: figure;
    }}
    a {{ color: var(--teal); text-decoration: none; }}
    p, li {{ widows: 3; orphans: 3; }}
    code {{
      font-family: "IBM Plex Mono", Menlo, Consolas, monospace;
      background: #ece6da;
      color: #16324f;
      padding: 2px 5px;
      border-radius: 5px;
      font-size: 10.7px;
    }}
    pre {{
      margin: 8px 0 0;
      padding: 10px 12px;
      border-radius: 12px;
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
      min-height: 245mm;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      padding: 12mm 10mm;
      break-after: page;
    }}
    .half-title-kicker {{
      margin: 0 0 10mm;
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
      margin: 10mm 0 0;
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
      border-radius: 20px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.94), rgba(248, 242, 230, 0.98)),
        linear-gradient(135deg, #f6f0e3 0%, #fffdf7 100%);
      color: var(--ink);
      box-shadow: var(--shadow);
      margin-bottom: 12px;
      border: 1px solid #d7cfbf;
    }}
    .cover::after {{
      content: "";
      position: absolute;
      right: 24px;
      top: 22px;
      width: 170px;
      height: 170px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(36, 54, 75, 0.08), rgba(36, 54, 75, 0.02) 58%, transparent 60%);
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
      border: 1px solid #d8cdb8;
      border-radius: 12px;
      background: rgba(255,255,255,0.6);
      padding: 9px 10px;
      font-size: 10px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .meta .k b {{ display: block; margin-top: 4px; font-size: 12px; color: var(--navy); }}
    .imprint-page {{
      page: imprint;
      min-height: 245mm;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10mm 0;
      break-after: page;
    }}
    .imprint-box {{
      width: 100%;
      max-width: 760px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: linear-gradient(180deg, #fffef9, #f8f2e8);
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
      border-top: 1px solid rgba(158, 106, 46, 0.22);
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
      border-radius: 16px;
      overflow: hidden;
      background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(247,240,226,0.98));
      border: 1px solid #d8cdb8;
      box-shadow: 0 12px 30px rgba(25, 37, 47, 0.08);
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
      border-radius: 18px;
      padding: 16px 16px 14px;
      margin: 14px 0;
      box-shadow: var(--shadow);
    }}
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
      border-radius: 14px;
      background: linear-gradient(180deg, #fffef9, #f8f2e8);
      padding: 12px;
      page-break-inside: avoid;
    }}
    .card.alt {{ background: linear-gradient(180deg, #fbf6eb, #fffef9); }}
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
      background: #ece7db;
      color: #304c52;
      font-size: 10px;
      font-weight: 700;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 10.7px; margin-top: 8px; page-break-inside: auto; }}
    th, td {{ border: 1px solid #d9e4f0; padding: 7px; vertical-align: top; text-align: left; }}
    th {{ background: #eee7d7; color: #17314b; font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif; }}
    thead {{ display: table-header-group; }}
    tfoot {{ display: table-footer-group; }}
    tr {{ page-break-inside: avoid; page-break-after: auto; }}
    .toc ol, .toc ul, ul, ol {{ margin: 6px 0 6px 18px; padding: 0; }}
    li {{ margin: 3px 0; }}
    .toc-groups {{ margin-top: 10px; }}
    .toc-group {{
      border: 1px solid #e3dccf;
      border-radius: 12px;
      background: linear-gradient(180deg, #fffef9, #f8f2e8);
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
      border-radius: 14px;
      background: #fdfaf2;
      padding: 8px;
      margin: 10px 0 0;
      text-align: center;
      page-break-inside: avoid;
      counter-increment: figure;
    }}
    .figure img {{ width: 100%; max-width: 860px; height: auto; border-radius: 8px; display: block; margin: 0 auto; }}
    .figure.narrow img {{ max-width: 620px; }}
    .figure.ui-shot img {{ max-width: 940px; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12); }}
    .caption {{ margin: 6px 0 0; font-size: 10.2px; color: var(--muted); text-align: left; }}
    .caption::before {{
      content: "Figure " counter(figure) ". ";
      color: var(--navy);
      font-weight: 700;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .gallery {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .figure-card {{
      border: 1px solid var(--line);
      border-radius: 14px;
      background: linear-gradient(180deg, #fffef9, #f6efe4);
      padding: 10px;
      display: grid;
      grid-template-columns: 0.95fr 1.05fr;
      gap: 10px;
      align-items: start;
      page-break-inside: avoid;
      counter-increment: figure;
    }}
    .figure-card img {{ width: 100%; height: auto; border-radius: 10px; background: #f8fbff; }}
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
    .cluster-head {{ display: grid; grid-template-columns: 1.3fr 0.9fr; gap: 12px; align-items: start; margin-bottom: 10px; }}
    .chapter-opener {{
      border: 1px solid var(--line);
      border-radius: 18px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248, 242, 230, 0.98)),
        linear-gradient(135deg, #f8f2e7 0%, #fffef9 100%);
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
      border-radius: 14px;
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
      border: 1px solid #d3c7b1;
      background: #f8f2e5;
      color: #4b5563;
      font-size: 9.8px;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    }}
    .cluster {{ break-before: auto; }}
    .case {{ border-top: 1px dashed #c7bba6; padding-top: 12px; margin-top: 12px; page-break-inside: avoid; }}
    .case:first-of-type {{ border-top: none; padding-top: 0; margin-top: 0; }}
    .case-head {{ display: grid; grid-template-columns: 1.25fr 0.95fr; gap: 12px; align-items: start; }}
    .case-meta {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; font-size: 10.4px; }}
    .case-meta > div {{ border: 1px solid var(--line); border-radius: 12px; padding: 8px; background: var(--panel); }}
    .case-meta b {{ display: block; color: var(--muted); margin-bottom: 4px; font-size: 9.8px; text-transform: uppercase; letter-spacing: 0.06em; font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif; }}
    .case-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 10px; }}
    .narrative h4 {{ margin: 0 0 4px; font-size: 12px; color: var(--navy); }}
    .study-note, .stepbox, .resultbox, .expected, .interpret, .biology {{
      margin-top: 10px;
      border-radius: 14px;
      padding: 10px 12px;
      page-break-inside: avoid;
    }}
    .study-note {{ border: 1px solid #d3c7b1; background: #faf3e8; }}
    .stepbox {{ border: 1px solid #c9d8dc; background: #f4f9f9; }}
    .resultbox {{ border: 1px solid #d8d3c9; background: #fbf8f1; }}
    .expected {{ border: 1px solid #d6dfcf; background: #f8fcf5; }}
    .interpret {{ border: 1px solid #e4d7ab; background: #fff9eb; }}
    .biology {{ border: 1px solid #e5cdd6; background: #fcf4f7; }}
    .study-note b, .stepbox b, .resultbox b, .expected b, .interpret b, .biology b {{ display: block; margin-bottom: 4px; color: var(--navy); font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif; }}
    .cluster, .case, .card, .figure, pre {{ page-break-inside: avoid; }}
    @media print {{
      body {{ background: #ffffff; }}
      .doc {{ max-width: none; margin: 0; padding: 0; }}
      .section, .cover, .card, .figure, .figure-card, .cover-shot, .imprint-box {{
        box-shadow: none;
      }}
      .section {{
        border-radius: 14px;
      }}
      .print-only {{ display: block; }}
      .cluster-head {{ display: none; }}
    }}
    @media screen {{
      .print-only {{ display: none !important; }}
    }}
  </style>
</head>
<body>
  <main class="doc">
    {render_half_title_page()}

    <section class="cover">
      <p class="eyebrow">Genome Forge {escape(APP_VERSION)} · Textbook Edition</p>
      <h1>Teach Yourself Bioinformatics with Genome Forge</h1>
      <p class="deck">A publication-style course reader for engineers, analysts, and curious scientists who want to learn bioinformatics by working through real laboratory molecules: reporter genes, cloning vectors, ambiguity-bearing consensus sequences, and clinically important genomic DNA.</p>
      <p>Instead of generic toy examples, the course uses public-source records such as EGFP, mCherry, pUC19/lacZ logic, and a BRAF exon 15 hotspot fragment. Clearly labelled training derivatives appear only where they sharpen a teaching goal, such as variant interpretation, family-wide assay design, or how to preserve uncertainty with IUPAC ambiguity symbols.</p>
      <div class="meta">
        <div class="k">Mode<b>Self-study course</b></div>
        <div class="k">Cases<b>{case_count} total lessons</b></div>
        <div class="k">Audience<b>CS to biology bridge</b></div>
        <div class="k">Release<b>{escape(TODAY)}</b></div>
      </div>
      {render_cover_spread()}
      <p class="cover-note">This edition is written to be read like a lab-ready monograph: each lesson combines software procedure, expected results, biological interpretation, and the reason the data matter in practice.</p>
    </section>

    {render_imprint_page(case_count)}

    {render_publication_note(case_count)}

    <section class="section">
      <p class="section-kicker">Using This Edition</p>
      <h2>How to Start and What Makes This Edition Different</h2>
      <div class="grid2">
        <div class="card">
          <h3>Quickstart</h3>
          <p>1. Start the web UI with <code>python3 web_ui.py --port 8080</code>.</p>
          <p>2. Materialize a case bundle with <code>{escape(case_bundle_command('A'))}</code>.</p>
          <p>3. Open <code>http://127.0.0.1:8080</code>, load the FASTA from your case bundle, and follow the matching case steps below.</p>
        </div>
        <div class="card alt">
          <h3>Why This Edition Is Different</h3>
          <p>This version explains what the input data actually are, why the task matters biologically, what a meaningful result would look like, and what you should and should not conclude from the output.</p>
          <p>Each lesson is designed so the numbers point to a real scientific story rather than a generic demo, and the newer ambiguity-aware methods are taught directly instead of being buried as silent implementation details.</p>
        </div>
      </div>
    </section>

    <section class="section">
      <p class="section-kicker">Orientation</p>
      <h2>Meaningful Results Preview</h2>
      <p class="muted">These quick facts are derived directly from the bundled records. They are here to orient you before you dive into the {case_count} hands-on lessons.</p>
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
          <p>Always save the exact case bundle you used. That keeps the tutorial reproducible and prevents “I think I loaded the right sequence” problems. Every case already ships with a prebuilt bundle, so you can start quickly and still regenerate it later if you want to inspect provenance.</p>
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
      <p class="section-kicker">Reference</p>
      <h2>Primer on Ambiguity Codes</h2>
      <p class="muted">Several later lessons now teach ambiguity-aware matching directly. These symbols do not mean the sequence is broken. They mean the evidence still permits a small set of bases at a position, and Genome Forge can now search, compare, and design around that uncertainty.</p>
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
      <p class="muted">These illustrations are included to help you recognize what Genome Forge is trying to show you in each workflow: structure, evidence, divergence, and provenance.</p>
      {render_visual_gallery()}
    </section>

    <section class="section">
      <p class="section-kicker">Biological Objects</p>
      <h2>Real-World Record Field Guide</h2>
      <p>These are the biological objects that power the tutorial. Some are public-source sequences bundled directly in the FASTA file. Others are clearly labelled training derivatives created from those public records so specific comparison cases have an answer key.</p>
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
      <p class="muted">Recommended order if you are new to biology: Cluster A → B → C → D → G → E → F → H.</p>
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
  </main>
</body>
</html>
''')


def build_case_inputs() -> list[dict]:
    return [
        {
            'case_id': case_info['id'],
            'title': case_info['title'],
            'cluster': case_info['cluster'],
            'records': case_info['records'],
            'tab': case_info['tab'],
            'workflow': case_info['workflow'],
            'apis': case_info['apis'],
            'extract_command': case_bundle_command(case_info['id']),
            'prebuilt_bundle_dir': f'docs/tutorial/datasets/case_bundles/case_{case_info["id"].lower()}',
        }
        for case_info in CASES
    ]


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
            lines.extend([
                f'## Case {case_info["id"]}: {case_info["title"]}',
                '',
                f'- Cluster: {cluster_titles[case_info["cluster"]]}',
                f'- Focus: {case_info["biological_question"]}',
                f'- Records: {", ".join(case_info["records"])}',
                f'- Workflow: {case_info["workflow"]}',
                f'- APIs: {", ".join(case_info["apis"])}',
                f'- Extract bundle: `{case_bundle_command(case_info["id"])} `'.rstrip(),
                f'- Key expected signal: {case_info["expected"][0]}',
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
