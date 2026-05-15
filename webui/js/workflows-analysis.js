async function runProteinEdit() {
  try {
    const r = await callApi('/api/protein-edit', payload({
      aa_index_1based: Number(document.getElementById('proteinEditAaIndex').value),
      new_residue: document.getElementById('proteinEditResidue').value,
      frame: Number(document.getElementById('frame').value),
      host: document.getElementById('host').value,
    }));
    document.getElementById('content').value = `>${r.name}\n${r.sequence}`;
    pushHistory(getContentValue());
    runInfo();
    show(r);
  } catch (e) { show(String(e)); }
}

async function runPairwiseAlign() {
  try {
    show(await callApi('/api/pairwise-align', {
      seq_a: document.getElementById('seqA').value,
      seq_b: document.getElementById('seqB').value,
      mode: document.getElementById('pairwiseMode').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runMultiAlign() {
  try {
    const sequences = document.getElementById('multiAlignSeqs').value.split('\n').map(s => s.trim()).filter(Boolean);
    show(await callApi('/api/multi-align', { sequences }));
  } catch (e) { show(String(e)); }
}

async function runMSA() {
  try {
    const sequences = document.getElementById('multiAlignSeqs').value.split('\n').map(s => s.trim()).filter(Boolean);
    const method = document.getElementById('msaMethod').value;
    const r = await callApi('/api/msa', { sequences, method });
    lastMSAAlignment = r.alignment || [];
    show(r);
  } catch (e) { show(String(e)); }
}

async function runAlignmentConsensus() {
  try {
    let alignment = lastMSAAlignment;
    if (!alignment || !alignment.length) {
      const sequences = document.getElementById('multiAlignSeqs').value.split('\n').map(s => s.trim()).filter(Boolean);
      const r = await callApi('/api/msa', { sequences, method: document.getElementById('msaMethod').value });
      alignment = r.alignment || [];
      lastMSAAlignment = alignment;
    }
    show(await callApi('/api/alignment-consensus', { alignment }));
  } catch (e) { show(String(e)); }
}

async function runMSAHeatmap() {
  try {
    let alignment = lastMSAAlignment;
    if (!alignment || !alignment.length) {
      const sequences = document.getElementById('multiAlignSeqs').value.split('\n').map(s => s.trim()).filter(Boolean);
      const r = await callApi('/api/msa', { sequences, method: document.getElementById('msaMethod').value });
      alignment = r.alignment || [];
      lastMSAAlignment = alignment;
    }
    const r = await callApi('/api/alignment-heatmap-svg', { alignment });
    setSvgContent('msaHeatmap', r.svg || '');
    show({ row_count: r.row_count, heatmap_rendered: true });
  } catch (e) { show(String(e)); }
}

async function runPhyloTree() {
  try {
    const sequences = document.getElementById('multiAlignSeqs').value.split('\n').map(s => s.trim()).filter(Boolean);
    show(await callApi('/api/phylo-tree', { sequences }));
  } catch (e) { show(String(e)); }
}

async function runAutoAnnotate() {
  try {
    const r = await callApi('/api/annotate-auto', payload());
    featureState = (r.annotations || []).map(a => ({
      key: a.type || 'misc_feature',
      location: `${a.start_1based}..${a.end_1based}`,
      qualifiers: { label: a.label || a.motif || 'auto' },
    }));
    show({ ...r, features_loaded: featureState.length });
  } catch (e) { show(String(e)); }
}

async function runAnnotDbSave() {
  try {
    const signatures = JSON.parse(document.getElementById('annotDbSigs').value);
    show(await callApi('/api/annot-db-save', {
      db_name: document.getElementById('annotDbName').value,
      signatures,
    }));
  } catch (e) { show(String(e)); }
}

async function runAnnotDbList() {
  try {
    show(await callApi('/api/annot-db-list', {}));
  } catch (e) { show(String(e)); }
}

async function runAnnotDbLoad() {
  try {
    const r = await callApi('/api/annot-db-load', {
      db_name: document.getElementById('annotDbName').value,
    });
    document.getElementById('annotDbSigs').value = JSON.stringify(r.signatures || [], null, 2);
    show(r);
  } catch (e) { show(String(e)); }
}

async function runAnnotDbApply() {
  try {
    const r = await callApi('/api/annot-db-apply', payload({
      db_name: document.getElementById('annotDbName').value,
    }));
    featureState = (r.annotations || []).map(a => ({
      key: a.type || 'misc_feature',
      location: `${a.start_1based}..${a.end_1based}`,
      qualifiers: { label: a.label || a.motif || 'db_annot' },
    }));
    show({ ...r, features_loaded: featureState.length });
  } catch (e) { show(String(e)); }
}

async function runAnnealOligos() {
  try {
    show(await callApi('/api/anneal-oligos', {
      forward: document.getElementById('oligoF').value,
      reverse: document.getElementById('oligoR').value,
      min_overlap: Number(document.getElementById('minOverlap').value),
    }));
  } catch (e) { show(String(e)); }
}

async function runMutagenesis() {
  try {
    show(await callApi('/api/mutagenesis', payload({
      start: Number(document.getElementById('editStart').value),
      end: Number(document.getElementById('editEnd').value),
      mutant: document.getElementById('editValue').value,
    })));
  } catch (e) { show(String(e)); }
}

async function runGelSim() {
  try {
    show(await callApi('/api/gel-sim', {
      sizes: document.getElementById('gelSizes').value,
      marker_set: document.getElementById('gelMarkerSet').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runGelMarkerSets() {
  try {
    show(await callApi('/api/gel-marker-sets', {}));
  } catch (e) { show(String(e)); }
}

async function runGelLadderSave() {
  try {
    const r = await callApi('/api/gel-ladder-save', {
      ladder_name: document.getElementById('gelLadderName').value,
      sizes: document.getElementById('gelLadderSizes').value,
    });
    show(r);
  } catch (e) { show(String(e)); }
}

async function runGelLadderLoad() {
  try {
    const r = await callApi('/api/gel-ladder-load', {
      ladder_name: document.getElementById('gelLadderName').value,
    });
    document.getElementById('gelLadderSizes').value = (r.sizes || []).join(',');
    show(r);
  } catch (e) { show(String(e)); }
}

async function runGelLadderList() {
  try {
    show(await callApi('/api/gel-ladder-list', {}));
  } catch (e) { show(String(e)); }
}

async function runDigestGel() {
  try {
    const r = await callApi('/api/digest-gel', payload({
      enzymes: document.getElementById('enzymes').value,
      enzyme_set: document.getElementById('enzymeSetName').value,
      marker_set: document.getElementById('gelLadderName').value || document.getElementById('gelMarkerSet').value,
    }));
    setDecisionCard('custom_ladder', r, {
      evidence: `Digest gel rendered with marker set ${document.getElementById('gelLadderName').value || document.getElementById('gelMarkerSet').value}.`,
    });
    show(r);
  } catch (e) { show(String(e)); }
}

function renderRestrictionCompare(result) {
  const rows = (result.diagnostic_candidates || []).slice(0, 40).map((row) => (
    `<tr><td>${escapeHtml(row.enzyme)}</td><td>${escapeHtml(row.site)}</td>` +
    `<td>${row.count_a}</td><td>${row.count_b}</td><td>${row.delta_a_minus_b}</td>` +
    `<td>${escapeHtml(row.category)}</td></tr>`
  )).join('');
  document.getElementById('restrictionCompareViz').innerHTML = `
    <table class="star-grid">
      <thead><tr><th>Enzyme</th><th>Site</th><th>A cuts</th><th>B cuts</th><th>Delta</th><th>Use case</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="6">No discriminatory cutters with current criteria.</td></tr>'}</tbody>
    </table>
  `;
}

async function runRestrictionCompare() {
  try {
    const r = await callApi('/api/restriction-compare', payload({
      sequence_b: document.getElementById('restrictionCompareSeq').value,
      enzymes: document.getElementById('enzymes').value,
      enzyme_set: document.getElementById('enzymeSetName').value,
      min_delta: Number(document.getElementById('restrictionMinDelta').value),
    }));
    renderRestrictionCompare(r);
    setDecisionCard('diagnostic_digest', r);
    show({ diagnostic_count: r.diagnostic_count, enzyme_count: r.enzyme_count, top: (r.diagnostic_candidates || []).slice(0, 5) });
  } catch (e) { show(String(e)); }
}

function renderSilentSites(result) {
  const rows = (result.candidates || []).slice(0, 80).map((row, idx) => (
    `<tr data-silent-site="${idx}"><td>${escapeHtml(row.enzyme)}</td><td>${escapeHtml(row.site)}</td>` +
    `<td>${row.site_start_1based}..${row.site_end_1based}</td><td>${row.protein_position_1based}</td>` +
    `<td>${escapeHtml(row.aa)} ${escapeHtml(row.original_codon)}-&gt;${escapeHtml(row.silent_codon)}</td>` +
    `<td>${escapeHtml((row.mutations || []).map((m) => `${m.position_1based}:${m.from}>${m.to}`).join(', '))}</td></tr>`
  )).join('');
  const host = document.getElementById('silentSitesViz');
  host.innerHTML = `
    <table class="star-grid">
      <thead><tr><th>Enzyme</th><th>Site</th><th>DNA site</th><th>AA #</th><th>Silent codon</th><th>Mutations</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="6">No silent restriction sites found for current enzyme set/frame.</td></tr>'}</tbody>
    </table>
  `;
  host.querySelectorAll('[data-silent-site]').forEach((row) => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', async () => {
      const hit = result.candidates[Number(row.getAttribute('data-silent-site'))];
      if (!hit) return;
      setTrackWindow(Math.max(1, hit.site_start_1based - 40), hit.site_end_1based + 40);
      setInspectorText(
        `Silent restriction candidate\n${hit.enzyme} ${hit.site}\n` +
        `Site: ${hit.site_start_1based}..${hit.site_end_1based}\n` +
        `Codon: ${hit.original_codon} -> ${hit.silent_codon} (${hit.aa})`
      );
      await runSequenceTrack();
    });
  });
}

async function runSilentRestrictionSites() {
  try {
    const r = await callApi('/api/silent-restriction-sites', payload({
      enzymes: document.getElementById('enzymes').value,
      enzyme_set: document.getElementById('enzymeSetName').value,
      frame: Number(document.getElementById('frame').value),
      max_candidates: Number(document.getElementById('silentMaxCandidates').value),
    }));
    renderSilentSites(r);
    setDecisionCard('silent_site', r);
    show({ candidate_count: r.candidate_count, frame: r.frame, truncated: r.truncated });
  } catch (e) { show(String(e)); }
}

async function runTranslatedFeatures() {
  try {
    show(await callApi('/api/translated-features', payload({
      include_slippage: document.getElementById('includeSlippage').checked,
      slip_pos_1based: Number(document.getElementById('slipPos').value),
      slip_type: document.getElementById('slipType').value,
    })));
  } catch (e) { show(String(e)); }
}

async function runTranslatedFeatureEdit() {
  try {
    const r = await callApi('/api/translated-feature-edit', payload({
      feature_index: Number(document.getElementById('editFeatureIndex').value),
      aa_index_1based: Number(document.getElementById('editAaIndex').value),
      new_residue: document.getElementById('editResidue').value,
      host: document.getElementById('host').value,
    }));
    document.getElementById('content').value = `>${r.name}\n${r.sequence}`;
    pushHistory(getContentValue());
    runInfo();
    show(r);
  } catch (e) { show(String(e)); }
}

async function runCdnaMap() {
  try {
    show(await callApi('/api/cdna-map', {
      cdna_sequence: document.getElementById('cdnaSeq').value,
      genome_sequence: document.getElementById('genomeSeq').value,
      min_exon_bp: Number(document.getElementById('cdnaMinExon').value),
      max_intron_bp: Number(document.getElementById('cdnaMaxIntron').value),
    }));
  } catch (e) { show(String(e)); }
}

async function runBatchDigest() {
  try {
    const records = JSON.parse(document.getElementById('batchRecords').value);
    show(await callApi('/api/batch-digest', {
      records,
      enzymes: document.getElementById('enzymes').value,
    }));
  } catch (e) { show(String(e)); }
}


async function runContigAssemble() {
  try {
    const reads = document.getElementById('contigReads').value.split('\n').map(s => s.trim()).filter(Boolean);
    show(await callApi('/api/contig-assemble', {
      reads,
      min_overlap: Number(document.getElementById('contigOverlap').value),
    }));
  } catch (e) { show(String(e)); }
}
