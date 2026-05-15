async function runInfo() {
  try {
    const info = await callApi('/api/info', payload());
    setStats(info);
    show(info);
  } catch (e) { show(String(e)); }
}

async function runTranslate(toStop) {
  try {
    const frame = Number(document.getElementById('frame').value);
    show(await callApi('/api/translate', payload({ frame, to_stop: !!toStop })));
  } catch (e) { show(String(e)); }
}

async function runDigest() {
  try {
    const r = await callApi('/api/digest', payload({
      enzymes: document.getElementById('enzymes').value,
      enzyme_set: document.getElementById('enzymeSetName').value,
    }));
    setDecisionCard('diagnostic_digest', { diagnostic_count: (r.fragments || []).length }, {
      title: 'Digest Evidence-to-Decision',
      evidence: `Digest returned ${(r.fragments || []).length} fragment(s) for the selected enzyme set.`,
      inference: 'Fragment sizes are the expected physical readout if the digest chemistry and topology assumptions hold.',
      limit: 'Fragment counts are only interpretable when topology, enzyme set, and methylation state match the real sample.',
      next: 'Compare predicted fragments with a ladder plan before using the digest as verification evidence.',
    });
    show(r);
  } catch (e) { show(String(e)); }
}

async function runMap() {
  try {
    const r = await callApi('/api/map', payload({ enzymes: document.getElementById('enzymes').value }));
    document.getElementById('map').innerHTML = r.svg;
    enhancePanel('map');
    setDecisionCard('map');
    show('Map rendered.');
  } catch (e) { show(String(e)); }
}

async function runSequenceTrack() {
  try {
    const [start, end] = trackWindow();
    setTrackWindow(start, end);
    const r = await callApi('/api/sequence-tracks', payload({
      start,
      end,
      frame: Number(document.getElementById('trackFrame').value),
    }));
    document.getElementById('seqTrack').innerHTML = r.svg;
    enhancePanel('seqTrack');
    show({ track_window: `${r.start_1based}..${r.end_1based}`, frame: r.frame });
  } catch (e) { show(String(e)); }
}

async function runTextMap() {
  try {
    const [start, end] = trackWindow();
    const r = await callApi('/api/text-map', payload({
      start,
      end,
      width: Number(document.getElementById('textMapWidth').value),
      frame: Number(document.getElementById('trackFrame').value),
    }));
    document.getElementById('textMapViz').innerHTML = `<pre>${escapeHtml(r.text_map || '')}</pre>`;
    setDecisionCard('text_map', r, {
      evidence: `Text map rendered ${r.chunk_count ?? 0} chunk(s) across ${r.start_1based}..${r.end_1based}.`,
    });
    show({ text_map_range: `${r.start_1based}..${r.end_1based}`, chunks: r.chunk_count, features: r.feature_count });
  } catch (e) { show(String(e)); }
}

async function runPrimerDesign() {
  try {
    const r = await callApi('/api/primers', payload({
      target_start: Number(document.getElementById('targetStart').value),
      target_end: Number(document.getElementById('targetEnd').value),
      window: Number(document.getElementById('window').value),
    }));
    document.getElementById('forward').value = r.forward.sequence;
    document.getElementById('reverse').value = r.reverse.sequence;
    setDecisionCard('generic', r, {
      title: 'Primer Evidence-to-Decision',
      evidence: `Primer pair proposed with forward ${r.forward.sequence.length} nt and reverse ${r.reverse.sequence.length} nt.`,
      inference: 'The pair is a candidate assay, not yet a proven experimental readout.',
      limit: 'Primer usefulness depends on specificity, Tm compatibility, product size, and controls.',
      next: 'Run primer diagnostics and virtual PCR before ordering or using the pair.',
    });
    show(r);
  } catch (e) { show(String(e)); }
}

async function runPcr() {
  try {
    show(await callApi('/api/pcr', payload({
      forward: document.getElementById('forward').value,
      reverse: document.getElementById('reverse').value,
    })));
  } catch (e) { show(String(e)); }
}

async function runPrimerDiagnostics() {
  try {
    show(await callApi('/api/primer-diagnostics', {
      forward: document.getElementById('forward').value,
      reverse: document.getElementById('reverse').value,
      na_mM: Number(document.getElementById('naMm').value),
      primer_nM: Number(document.getElementById('primerNm').value),
    }));
  } catch (e) { show(String(e)); }
}

async function runPcrGelLanes() {
  try {
    const primer_pairs = JSON.parse(document.getElementById('pcrLanePairs').value);
    show(await callApi('/api/pcr-gel-lanes', payload({
      primer_pairs,
      marker_set: document.getElementById('gelMarkerSet').value,
    })));
  } catch (e) { show(String(e)); }
}

async function runCodonOptimize() {
  try {
    const frame = Number(document.getElementById('frame').value);
    show(await callApi('/api/codon-optimize', payload({ host: document.getElementById('host').value, frame })));
  } catch (e) { show(String(e)); }
}

async function runMotif() {
  try {
    show(await callApi('/api/motif', payload({ motif: document.getElementById('motif').value })));
  } catch (e) { show(String(e)); }
}

async function runOrfs() {
  try {
    show(await callApi('/api/orfs', payload({ min_aa: Number(document.getElementById('minAa').value) })));
  } catch (e) { show(String(e)); }
}

async function runSearchEntities() {
  try {
    show(await callApi('/api/search-entities', payload({
      query: document.getElementById('entityQuery').value,
      primers: document.getElementById('searchPrimers').value,
    })));
  } catch (e) { show(String(e)); }
}

async function runEnzymeScan() {
  try {
    show(await callApi('/api/enzyme-scan', payload({
      enzyme_set: document.getElementById('enzymeSetName').value,
    })));
  } catch (e) { show(String(e)); }
}

async function runEnzymeInfo() {
  try {
    show(await callApi('/api/enzyme-info', {
      enzymes: document.getElementById('enzymes').value,
      enzyme_set: document.getElementById('enzymeSetName').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runDigestAdvanced() {
  try {
    show(await callApi('/api/digest-advanced', payload({
      enzymes: document.getElementById('enzymes').value,
      enzyme_set: document.getElementById('enzymeSetName').value,
      methylated_motifs: document.getElementById('methylMotifs').value,
    })));
  } catch (e) { show(String(e)); }
}

function renderStarViz(scan) {
  const host = document.getElementById('starViz');
  const hits = Array.isArray(scan.star_hits) ? scan.star_hits : [];
  const byEnzyme = {};
  for (const h of hits) byEnzyme[h.enzyme] = (byEnzyme[h.enzyme] || 0) + 1;
  const rank = Object.entries(byEnzyme).sort((a, b) => b[1] - a[1]);
  const maxCount = rank.length ? rank[0][1] : 1;

  const summary = `
    <div class="star-summary">
      <div class="star-chip"><small>Star Hits</small><b>${scan.star_hit_count || 0}</b></div>
      <div class="star-chip"><small>Level</small><b>${Number(scan.star_activity_level || 0).toFixed(2)}</b></div>
      <div class="star-chip"><small>Max Mismatch</small><b>${scan.max_mismatch ?? 0}</b></div>
      <div class="star-chip"><small>Enzymes Flagged</small><b>${rank.length}</b></div>
    </div>
  `;
  const rows = rank.length
    ? rank.map(([enzyme, count]) => {
        const width = Math.max(2, Math.round((count / maxCount) * 100));
        return `<tr><td>${escapeHtml(enzyme)}</td><td>${count}</td><td><div class="bar" style="width:${width}%"></div></td></tr>`;
      }).join('')
    : '<tr><td colspan="3">No off-target cuts detected for current level.</td></tr>';
  const table = `
    <table class="star-grid">
      <thead><tr><th>Enzyme</th><th>Off-target sites</th><th>Relative burden</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  host.innerHTML = summary + table;
  const topHits = hits.slice(0, 12).map((h) => (
    `<tr data-star-cut="${h.cut_position_1based}" title="Jump to ${h.cut_position_1based}">` +
    `<td>${escapeHtml(h.enzyme)}</td><td>${h.cut_position_1based}</td><td>${h.mismatches}</td><td>${escapeHtml(h.matched)}</td></tr>`
  )).join('');
  if (topHits) {
    host.innerHTML += `
      <table class="star-grid" style="margin-top:10px">
        <thead><tr><th>Enzyme</th><th>Cut pos</th><th>Mismatches</th><th>Matched site</th></tr></thead>
        <tbody>${topHits}</tbody>
      </table>
    `;
  }
  host.querySelectorAll('tr[data-star-cut]').forEach((row) => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', async () => {
      const p = Number(row.getAttribute('data-star-cut'));
      const len = Math.max(60, Number(document.getElementById('trackEnd').value) - Number(document.getElementById('trackStart').value));
      const seqLen = Number(document.getElementById('sLen').textContent) || 0;
      const start = Math.max(1, p - Math.floor(len / 2));
      const end = seqLen > 0 ? Math.min(seqLen, start + len) : (start + len);
      document.getElementById('trackStart').value = start;
      document.getElementById('trackEnd').value = end;
      setInspectorText(`Star cut selected\nPosition: ${p}\nTrack window centered and re-rendered.`);
      await runSequenceTrack();
    });
  });
}

async function runStarActivityScan() {
  try {
    const r = await callApi('/api/star-activity-scan', payload({
      enzymes: document.getElementById('enzymes').value,
      enzyme_set: document.getElementById('enzymeSetName').value,
      star_activity_level: Number(document.getElementById('starActivityLevel').value),
      include_star_cuts: document.getElementById('includeStarCuts').checked,
    }));
    renderStarViz(r);
    show(r);
  } catch (e) { show(String(e)); }
}

async function runEnzymeSetSave() {
  try {
    show(await callApi('/api/enzyme-set-save', {
      set_name: document.getElementById('enzymeSetName').value,
      enzymes: document.getElementById('enzymes').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runEnzymeSetLoad() {
  try {
    const r = await callApi('/api/enzyme-set-load', {
      set_name: document.getElementById('enzymeSetName').value,
    });
    document.getElementById('enzymes').value = (r.enzymes || []).join(',');
    show(r);
  } catch (e) { show(String(e)); }
}

async function runEnzymeSetList() {
  try {
    show(await callApi('/api/enzyme-set-list', {}));
  } catch (e) { show(String(e)); }
}

async function runPredefinedEnzymeSets() {
  try {
    show(await callApi('/api/enzyme-set-predefined', {}));
  } catch (e) { show(String(e)); }
}

async function runEnzymeSetDelete() {
  try {
    show(await callApi('/api/enzyme-set-delete', {
      set_name: document.getElementById('enzymeSetName').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runReverseTranslate() {
  try {
    show(await callApi('/api/reverse-translate', {
      protein: document.getElementById('protein').value,
      host: document.getElementById('host').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runCanonicalizeRecord() {
  try {
    show(await callApi('/api/canonicalize-record', payload({})));
  } catch (e) { show(String(e)); }
}

async function runConvertRecord() {
  try {
    show(await callApi('/api/convert-record', payload({
      target_format: document.getElementById('canonicalTargetFormat').value,
    })));
  } catch (e) { show(String(e)); }
}
