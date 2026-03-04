# Real-World Functional Test Report

- Date: 2026-03-04 11:20:39 EST
- Total Steps: 75
- Passed: 75
- Failed: 0

## Data Sources Used

- EGFP CDS (widely used GFP coding sequence, 720 bp including stop)
- mCherry CDS (widely used red fluorescent protein coding sequence)
- pUC19 MCS sequence (common cloning vector MCS region)

## Step-by-Step Results

| Step | Objective | Status | Time (ms) | Key Details / Error |
|---|---|---|---:|---|
| `info_egfp` | Compute basic stats for EGFP CDS | **PASS** | 1 | name=EGFP_CDS, length=720, topology=linear, gc=61.25 |
| `info_mcherry` | Compute basic stats for mCherry CDS | **PASS** | 0 | name=mCherry_CDS, length=711, topology=linear, gc=62.59 |
| `translate_egfp` | Translate EGFP coding sequence | **PASS** | 1 | protein=MVSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTLTYGVQCFSRYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTL... <240 chars total> |
| `translated_features_egfp` | Generate translated feature report from EGFP feature annotation | **PASS** | 1 | count=1, translated_features=<list:1> |
| `digest_puc_mcs` | Digest pUC19 MCS region with common restriction enzymes | **PASS** | 0 | topology=circular, cuts=[{'enzyme': '<str>', 'position_1based': '<int>'}, {'enzyme': '<str>', 'position_1based': '<int>'}, {'enzyme': '<str>', 'position_1based': '<int>'}, {'enzyme': '<str>', 'position_1based': '<int>'}, {'enzyme': '<str>', 'position_1based': '<int>'}, {'enzyme': '<str>', 'position_1based': '<int>'}], unique_cut_positions_1based=[2, 18, 23, 29, 45, 53], fragments_bp=[16, 16, 8, 6, 6, 5] |
| `digest_adv_methyl` | Run methylation-aware digest on pUC19 MCS | **PASS** | 0 | topology=circular, methylated_motifs=['GAATTC', 'GGATCC'], blocked_cuts=[{'enzyme': '<str>', 'site': '<str>', 'position_1based': '<int>'}, {'enzyme': '<str>', 'site': '<str>', 'position_1based': '<int>'}], cuts=[{'enzyme': '<str>', 'position_1based': '<int>'}] |
| `star_activity_scan` | Scan star activity risk on restriction panel | **PASS** | 1 | star_activity_level=0.65, max_mismatch=1, exact_digest={'topology': 'circular', 'cuts': ['<dict>', '<dict>', '<dict>'], 'unique_cut_positions_1based': ['<int>', '<int>', '<int>'], 'fragments_bp': ['<int>', '<int>', '<int>']}, star_hits=[] |
| `map_svg` | Render plasmid/linear map SVG | **PASS** | 1 | svg=<1969 chars> |
| `sequence_track_svg` | Render sequence track for coding region | **PASS** | 1 | start_1based=1, end_1based=180, frame=1, svg=<24705 chars> |
| `motif_search` | Find canonical EcoRI motif in pUC19 MCS | **PASS** | 0 | motif=GAATTC, count=1, positions_1based=[1] |
| `orf_scan` | Find ORFs in EGFP sequence | **PASS** | 1 | count=1, orfs=[{'start': '<int>', 'end': '<int>', 'frame': '<int>', 'aa_len': '<int>', 'protein_preview': '<str>'}] |
| `primer_design` | Design primers for EGFP internal region | **PASS** | 155 | forward_len=25, reverse_len=25 |
| `primer_diagnostics` | Evaluate primer thermodynamics and pair behavior | **PASS** | 1 | conditions={'na_mM': 50.0, 'primer_nM': 250.0}, forward={'length': 25, 'gc': 64.0, 'tm_wallace': 82.0, 'tm_nn': 60.763847880624326, 'gc_clamp': True, 'self_dimer_max_run': 4, 'self_end_dimer_run': 4, 'hairpin_stem': 0}, reverse={'length': 25, 'gc': 64.0, 'tm_wallace': 82.0, 'tm_nn': 59.93974896845049, 'gc_clamp': True, 'self_dimer_max_run': 4, 'self_end_dimer_run': 2, 'hairpin_stem': 0}, pair={'heterodimer_run': 7, 'heterodimer_3prime_run': 0, 'tm_delta': 0.82, 'predicted_risk_flags': []} |
| `virtual_pcr` | Simulate PCR amplification using designed EGFP primers | **PASS** | 0 | forward_hits=[71], reverse_hits=[508], products=<list:1> |
| `pcr_gel_lanes` | Simulate gel lanes for designed primer pair | **PASS** | 0 | marker_set=1kb_plus, marker_bands=[{'size_bp': '<int>', 'relative_migration': '<float>'}, {'size_bp': '<int>', 'relative_migration': '<float>'}, {'size_bp': '<int>', 'relative_migration': '<float>'}, '... (11 more)'], sample_bands=[{'size_bp': '<int>', 'relative_migration': '<float>'}], available_marker_sets=['100bp', '1kb_plus', 'high_range', 'ultra_low'] |
| `codon_optimize_yeast` | Codon-optimize EGFP for yeast host | **PASS** | 0 | protein=MVSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTLTYGVQCFSRYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTL... <240 chars total>, optimized_nt=ATGGTTTCTAAAGGTGAAGAATTGTTTACTGGTGTTGTTCCAATTTTGGTTGAATTGGATGGTGATGTTAATGGTCATAAATTTTCTGTTTCTGGTGAAGGTGAAGGTGATGCTACTTAT... <720 chars total>, gc_original=61.25, gc_optimized=29.17 |
| `canonicalize_record` | Convert EGFP record to canonical schema | **PASS** | 0 | canonical_record={'schema': '1.0.0', 'created_at': '2026-03-04T16:20:38.841385+00:00', 'source_format': 'fasta', 'record_id': '8f16e92af26c6f40', 'name': 'EGFP_CDS', 'molecule': 'DNA', 'topology': 'linear', 'length': 720, '...': '+5 keys'} |
| `convert_record_roundtrip` | Roundtrip canonical -> FASTA/GenBank/payload | **PASS** | 2 | fasta_len=741, genbank_len=1185 |
| `dna_export_import` | Export and import Genome Forge DNA container | **PASS** | 1 | source=genomeforge_dna, name=EGFP_CDS, length=720, topology=linear |
| `trace_import_align_consensus` | Synthetic trace import + align + consensus pipeline | **PASS** | 246 | trace_id=trace_5764ef34c9fc, length=720, min_quality=20, low_quality_bases=0 |
| `search_entities` | Search across features, enzymes, and primer hits | **PASS** | 0 | query=GFP, motif_hit_count=0, motif_hits=[], feature_hit_count=2 |
| `reverse_translate` | Reverse-translate protein motif into DNA | **PASS** | 0 | protein=MSTNPKPQRKTK, host=ecoli, dna=ATGTCGACCAACCCGAAACCGCAGCGTAAAACCAAA, length=36 |
| `protein_edit` | Edit amino acid in EGFP CDS and regenerate nucleotide sequence | **PASS** | 0 | edited=True, mode=protein_edit, frame=1, aa_index_1based=10 |
| `translated_feature_edit` | Apply AA edit through translated-feature editor | **PASS** | 0 | edited=True, feature_index=0, aa_index_1based=20, old_codon=GAC |
| `sequence_edit` | Apply nucleotide replacement edit in EGFP | **PASS** | 0 | name=EGFP_CDS, length=720, topology=linear, gc=61.53 |
| `mutagenesis` | Apply mutagenesis edit in EGFP region | **PASS** | 0 | start=40, end=45, mutant=GAGGAG, length=720 |
| `pairwise_dna` | Run pairwise DNA alignment between EGFP and mCherry | **PASS** | 128 | score=62, identity_pct=58.61, aligned_a=<749 chars>, aligned_b=<749 chars> |
| `pairwise_protein` | Run protein alignment between EGFP and mCherry | **PASS** | 14 | mode=protein, score=-52, identity_pct=30.89, aligned_a=<246 chars> |
| `multi_align_ref` | Reference-based multiple alignment of real CDS inputs | **PASS** | 178 | reference_length=720, sequence_count=3, pairwise_to_reference=<list:2> |
| `msa_progressive` | Progressive MSA on real coding sequences | **PASS** | 214 | rows=3, columns=749 |
| `msa_consensus` | Consensus generation from MSA | **PASS** | 2 | row_count=3, columns=749, consensus=ATGGTGAGCAAGGGCGAGGAGGATAACATGGCCTTCATCACGGAGGTGGTGCCCATCCTGGTCGAGCTGGACGGCGACGTAAACGGCCACAAGTTCGAGCGTGTCCGGCGAGGGCGAGGG... <749 chars total>, conservation=<list:749> |
| `msa_heatmap` | MSA identity heatmap SVG generation | **PASS** | 1 | row_count=3, svg=<3151 chars>, identity_matrix_pct=[['<float>', '<float>', '<float>'], ['<float>', '<float>', '<float>'], ['<float>', '<float>', '<float>']] |
| `phylo_tree` | Generate UPGMA phylogenetic tree from real sequences | **PASS** | 302 | sequence_count=3, merges=[{'left': '<int>', 'right': '<int>', 'distance': '<float>', 'new_id': '<int>', 'newick_partial': '<str>'}, {'left': '<int>', 'right': '<int>', 'distance': '<float>', 'new_id': '<int>', 'newick_partial': '<str>'}], newick=(S2:21.84,(S1:15.28,S3:15.28):21.84); |
| `anneal_oligos` | Simulate oligo annealing with realistic overhangs | **PASS** | 0 | forward_len=30, reverse_len=30, reverse_rc=GCACCACCCCGGTGAACAGCTCCTCGCCCT, overlap_bp=0 |
| `gel_sim` | Simulate agarose gel marker + product sizes | **PASS** | 0 | marker_set=100bp, marker_bands=[{'size_bp': '<int>', 'relative_migration': '<float>'}, {'size_bp': '<int>', 'relative_migration': '<float>'}, {'size_bp': '<int>', 'relative_migration': '<float>'}, '... (11 more)'], sample_bands=[{'size_bp': '<int>', 'relative_migration': '<float>'}, {'size_bp': '<int>', 'relative_migration': '<float>'}, {'size_bp': '<int>', 'relative_migration': '<float>'}, {'size_bp': '<int>', 'relative_migration': '<float>'}, {'size_bp': '<int>', 'relative_migration': '<float>'}], available_marker_sets=['100bp', '1kb_plus', 'high_range', 'ultra_low'] |
| `gel_marker_sets` | List available marker ladder sets | **PASS** | 0 | marker_sets={'1kb_plus': ['<int>', '<int>', '<int>', '... (11 more)'], '100bp': ['<int>', '<int>', '<int>', '... (11 more)'], 'ultra_low': ['<int>', '<int>', '<int>', '... (12 more)'], 'high_range': ['<int>', '<int>', '<int>', '... (10 more)']}, count=4 |
| `annotate_auto` | Auto-annotate EGFP sequence motifs | **PASS** | 1 | count=2, annotations=[{'label': '<str>', 'type': '<str>', 'motif': '<str>', 'start_1based': '<int>', 'end_1based': '<int>', 'frame': '<int>', 'aa_len': '<int>'}, {'label': '<str>', 'type': '<str>', 'motif': '<str>', 'start_1based': '<int>', 'end_1based': '<int>'}] |
| `annotation_db_save` | Save annotation DB with real motif signatures | **PASS** | 1 | saved=True, name=real_db_059424fb, count=2, path=/Users/liux17/Documents/Playground/annotation_db/real_db_059424fb.json |
| `annotation_db_list` | List annotation DB libraries | **PASS** | 1 | count=1, databases=[{'name': '<str>', 'updated_at': '<str>', 'count': '<int>', 'path': '<str>'}] |
| `annotation_db_load` | Load saved annotation DB | **PASS** | 1 | name=real_db_059424fb, updated_at=2026-03-04T16:20:39.944560+00:00, signatures=[{'label': '<str>', 'type': '<str>', 'motif': '<str>'}, {'label': '<str>', 'type': '<str>', 'motif': '<str>'}] |
| `annotation_db_apply` | Apply saved annotation DB to EGFP | **PASS** | 1 | db_name=real_db_059424fb, count=2, annotations=[{'label': '<str>', 'type': '<str>', 'motif': '<str>', 'start_1based': '<int>', 'end_1based': '<int>'}, {'label': '<str>', 'type': '<str>', 'motif': '<str>', 'start_1based': '<int>', 'end_1based': '<int>'}] |
| `features_list` | List feature entries on EGFP record | **PASS** | 0 | count=2, features=[{'key': '<str>', 'location': '<str>', 'qualifiers': '<dict>'}, {'key': '<str>', 'location': '<str>', 'qualifiers': '<dict>'}] |
| `features_add_update_delete` | Add, update, and delete a feature entry | **PASS** | 2 | count=1, features=[{'key': '<str>', 'location': '<str>', 'qualifiers': '<dict>'}] |
| `enzyme_scan` | Scan built-in enzymes against real sequence | **PASS** | 1 | hit_count=0, enzymes=[] |
| `enzyme_info` | Fetch metadata for common restriction enzymes | **PASS** | 0 | count=3, enzymes=[{'enzyme': '<str>', 'site': '<str>', 'cut_offset': '<int>', 'type': '<str>', 'methylation_blocked_by': '<list>'}, {'enzyme': '<str>', 'site': '<str>', 'cut_offset': '<int>', 'type': '<str>', 'methylation_blocked_by': '<list>'}, {'enzyme': '<str>', 'site': '<str>', 'cut_offset': '<int>', 'type': '<str>', 'methylation_blocked_by': '<list>'}] |
| `enzyme_set_predefined` | Enumerate predefined enzyme sets | **PASS** | 0 | count=4, sets=[{'name': '<str>', 'enzymes': '<list>', 'count': '<int>'}, {'name': '<str>', 'enzymes': '<list>', 'count': '<int>'}, {'name': '<str>', 'enzymes': '<list>', 'count': '<int>'}, {'name': '<str>', 'enzymes': '<list>', 'count': '<int>'}] |
| `enzyme_set_save` | Save custom enzyme panel | **PASS** | 1 | saved=True, name=real_set_059424fb, count=3, path=/Users/liux17/Documents/Playground/enzyme_sets/real_set_059424fb.json |
| `enzyme_set_list` | List custom enzyme panels | **PASS** | 1 | count=5, sets=[{'name': '<str>', 'updated_at': '<str>', 'count': '<int>', 'path': '<str>'}, {'name': '<str>', 'updated_at': '<str>', 'count': '<int>', 'path': '<str>', 'builtin': '<bool>'}, {'name': '<str>', 'updated_at': '<str>', 'count': '<int>', 'path': '<str>', 'builtin': '<bool>'}, {'name': '<str>', 'updated_at': '<str>', 'count': '<int>', 'path': '<str>', 'builtin': '<bool>'}, {'name': '<str>', 'updated_at': '<str>', 'count': '<int>', 'path': '<str>', 'builtin': '<bool>'}] |
| `enzyme_set_load` | Load custom enzyme panel | **PASS** | 0 | name=real_set_059424fb, updated_at=2026-03-04T16:20:39.955529+00:00, enzymes=['BamHI', 'EcoRI', 'HindIII'], notes= |
| `enzyme_set_delete` | Delete custom enzyme panel | **PASS** | 0 | deleted=True, name=real_set_059424fb |
| `batch_digest` | Run batch digest across multiple real records | **PASS** | 0 | count=3, results=[{'name': '<str>', 'length': '<int>', 'cuts': '<int>', 'fragments_bp': '<list>'}, {'name': '<str>', 'length': '<int>', 'cuts': '<int>', 'fragments_bp': '<list>'}, {'name': '<str>', 'length': '<int>', 'cuts': '<int>', 'fragments_bp': '<list>'}] |
| `cdna_map` | Map cDNA to genome using EGFP-derived exon model | **PASS** | 0 | cdna_length=210, genome_length=230, aligned_bp=210, coverage_pct=100.0 |
| `contig_assemble` | Assemble overlapping reads from EGFP sequence | **PASS** | 0 | input_reads=4, contig_count=1, largest_contig_length=720, steps=[{'left_idx': '<int>', 'right_idx': '<int>', 'overlap_bp': '<int>', 'merged_length': '<int>'}, {'left_idx': '<int>', 'right_idx': '<int>', 'overlap_bp': '<int>', 'merged_length': '<int>'}, {'left_idx': '<int>', 'right_idx': '<int>', 'overlap_bp': '<int>', 'merged_length': '<int>'}] |
| `gibson_assemble` | Gibson assembly with EGFP fragments | **PASS** | 0 | fragment_count=3, overlaps=[{'left_fragment': '<int>', 'right_fragment': '<int>', 'overlap_bp': '<int>', 'sequence': '<40 chars>'}, {'left_fragment': '<int>', 'right_fragment': '<int>', 'overlap_bp': '<int>', 'sequence': '<40 chars>'}], circular_overlap_bp=0, assembled_length=720 |
| `in_fusion` | In-Fusion assembly with overlapping EGFP fragments | **PASS** | 0 | fragment_count=3, joins=[{'left_fragment': '<int>', 'right_fragment': '<int>', 'homology_bp': '<int>'}, {'left_fragment': '<int>', 'right_fragment': '<int>', 'homology_bp': '<int>'}], closing_homology_bp=0, assembled_length=720 |
| `overlap_extension_pcr` | Overlap extension PCR from EGFP split fragments | **PASS** | 0 | overlap_bp=40, product_length=720, product_sequence=<720 chars> |
| `golden_gate` | Golden Gate simulation with realistic coding parts | **PASS** | 0 | part_count=2, joins=[{'left_part': '<int>', 'right_part': '<int>', 'left_overhang': '<str>', 'right_overhang': '<str>'}], closing_join_ok=None, assembled_length=180 |
| `gateway_cloning` | Gateway LR-style cloning simulation | **PASS** | 0 | insert_length=120, product_length=189, product_sequence=<189 chars> |
| `topo_cloning` | TOPO cloning simulation | **PASS** | 0 | mode=TA, product_length=207, product_sequence=<207 chars> |
| `ta_gc_cloning` | TA/GC cloning simulation | **PASS** | 0 | mode=GC, product_length=207, product_sequence=<207 chars> |
| `cloning_compatibility` | Compatibility check for restriction cloning setup | **PASS** | 0 | mode=restriction, ok=True, messages=['Restriction compatibility check passed'], checks={'EcoRI': {'site': '<str>', 'vector_sites': '<int>', 'insert_sites': '<int>'}, 'HindIII': {'site': '<str>', 'vector_sites': '<int>', 'insert_sites': '<int>'}} |
| `ligation_sim` | Predict ligation product distributions | **PASS** | 0 | vector_ends={'left': {'enzyme': '<str>', 'overhang': '<str>', 'polarity': '<str>'}, 'right': {'enzyme': '<str>', 'overhang': '<str>', 'polarity': '<str>'}}, insert_ends={'left': {'enzyme': '<str>', 'overhang': '<str>', 'polarity': '<str>'}, 'right': {'enzyme': '<str>', 'overhang': '<str>', 'polarity': '<str>'}}, derive_from_sequence=False, include_byproducts=True |
| `project_save` | Save a real-world project | **PASS** | 1 | saved=True, project_name=real_proj_059424fb, path=/Users/liux17/Documents/Playground/projects/real_proj_059424fb.json |
| `project_load` | Load saved project | **PASS** | 0 | project_name=real_proj_059424fb, updated_at=2026-03-04T16:20:39.966343+00:00, name=EGFP_CDS, topology=linear |
| `project_list` | List project catalog | **PASS** | 0 | count=1, projects=[{'project_name': '<str>', 'updated_at': '<str>', 'path': '<str>'}] |
| `project_history_graph` | Build project history graph data | **PASS** | 0 | project_name=real_proj_059424fb, node_count=2, nodes=[{'id': '<int>', 'label': '<str>', 'size': '<int>'}, {'id': '<int>', 'label': '<str>', 'size': '<int>'}], edges=[{'from': '<int>', 'to': '<int>'}] |
| `project_history_svg` | Render project history SVG | **PASS** | 0 | project_name=real_proj_059424fb, svg=<521 chars>, node_count=2, nodes=[{'id': '<int>', 'label': '<str>', 'size': '<int>'}, {'id': '<int>', 'label': '<str>', 'size': '<int>'}] |
| `collection_save` | Save collection with project | **PASS** | 0 | saved=True, collection_name=real_col_059424fb, count=1, path=/Users/liux17/Documents/Playground/collections/real_col_059424fb.json |
| `collection_load` | Load collection | **PASS** | 0 | collection_name=real_col_059424fb, updated_at=2026-03-04T16:20:39.970011+00:00, projects=['real_proj_059424fb'], notes= |
| `collection_list` | List collections | **PASS** | 0 | count=1, collections=[{'collection_name': '<str>', 'updated_at': '<str>', 'count': '<int>', 'path': '<str>'}] |
| `collection_add_project` | Add project to collection | **PASS** | 0 | saved=True, collection_name=real_col_059424fb, count=1, path=/Users/liux17/Documents/Playground/collections/real_col_059424fb.json |
| `share_create_load_get` | Create/load/share bundle over HTTP | **PASS** | 2 | share_id=5bb4c3779916, html_bytes=1577 |
| `collection_delete` | Delete collection | **PASS** | 0 | deleted=True, collection_name=real_col_059424fb |
| `project_delete` | Delete project | **PASS** | 0 | deleted=True, project_name=real_proj_059424fb |
| `root_page` | Ensure UI root page loads | **PASS** | 0 | contains_genome_forge=True |

## Conclusion

All real-world functional test steps passed.
