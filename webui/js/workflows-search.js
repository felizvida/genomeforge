async function runBlastSearch() {
  try {
    const dbRows = splitSeqLines('blastDb').map((sequence, i) => ({ name: `subject_${i+1}`, sequence }));
    show(await callApi('/api/blast-search', payload({
      query_sequence: document.getElementById('blastQuery').value,
      database_sequences: dbRows,
      kmer: Number(document.getElementById('blastKmer').value),
      top_hits: Number(document.getElementById('blastTopHits').value),
    })));
  } catch (e) { show(String(e)); }
}

async function runReferenceDbSave() {
  try {
    const elements = JSON.parse(document.getElementById('referenceDbElements').value);
    show(await callApi('/api/reference-db-save', {
      db_name: document.getElementById('referenceDbName').value,
      elements,
    }));
  } catch (e) { show(String(e)); }
}

async function runReferenceDbList() {
  try {
    show(await callApi('/api/reference-db-list', {}));
  } catch (e) { show(String(e)); }
}

async function runReferenceDbLoad() {
  try {
    const r = await callApi('/api/reference-db-load', {
      db_name: document.getElementById('referenceDbName').value,
    });
    if (Array.isArray(r.elements)) {
      document.getElementById('referenceDbElements').value = JSON.stringify(r.elements, null, 2);
    }
    show(r);
  } catch (e) { show(String(e)); }
}

async function runReferenceScan() {
  try {
    const r = await callApi('/api/reference-scan', payload({
      db_name: document.getElementById('referenceDbName').value,
      add_features: true,
    }));
    if (Array.isArray(r.features)) {
      featureState = r.features;
    }
    show(r);
  } catch (e) { show(String(e)); }
}

async function runSirnaDesign() {
  try {
    const r = await callApi('/api/sirna-design', payload({
      sequence: plainSeq(document.getElementById('content').value),
      min_len: Number(document.getElementById('sirnaMinLen').value),
      max_len: Number(document.getElementById('sirnaMaxLen').value),
      top_n: Number(document.getElementById('sirnaTopN').value),
    }));
    if (Array.isArray(r.candidates) && r.candidates.length) {
      document.getElementById('sirnaSequence').value = r.candidates[0].antisense_rna || r.candidates[0].target_dna || '';
    }
    show(r);
  } catch (e) { show(String(e)); }
}

async function runSirnaMap() {
  try {
    show(await callApi('/api/sirna-map', payload({
      sequence: plainSeq(document.getElementById('content').value),
      sirna_sequence: document.getElementById('sirnaSequence').value,
    })));
  } catch (e) { show(String(e)); }
}

async function runSequenceAnalyticsViz() {
  try {
    const r = await callApi('/api/sequence-analytics-svg', payload({
      start: Number(document.getElementById('analyticsStart').value),
      end: Number(document.getElementById('analyticsEnd').value),
      window: Number(document.getElementById('analyticsWindow').value),
      step: Number(document.getElementById('analyticsStep').value),
    }));
    document.getElementById('seqAnalyticsViz').innerHTML = r.svg || '';
    enhancePanel('seqAnalyticsViz');
    show({
      analytics_points: r.point_count,
      gc_mean: r.gc_mean,
      gc_range: [r.gc_min, r.gc_max],
      window: r.window,
      step: r.step,
    });
  } catch (e) { show(String(e)); }
}

async function runComparisonLensViz() {
  try {
    const seqA = document.getElementById('compareSeqA').value.trim();
    const seqB = document.getElementById('compareSeqB').value.trim();
    const r = await callApi('/api/comparison-lens-svg', payload({
      seq_a: seqA || undefined,
      seq_b: seqB,
      window: Number(document.getElementById('compareWindow').value),
    }));
    document.getElementById('compareLensViz').innerHTML = r.svg || '';
    enhancePanel('compareLensViz');
    show({
      identity_pct: r.identity_pct,
      alignment_length: r.alignment_length,
      hotspot_count: Array.isArray(r.hotspots) ? r.hotspots.length : 0,
      hotspots: r.hotspots || [],
    });
  } catch (e) { show(String(e)); }
}

async function runImportDna() {
  try {
    const r = await callApi('/api/import-dna', {
      dna_base64: document.getElementById('dnaBlob').value.trim(),
    });
    if (r.payload) {
      document.getElementById('name').value = r.payload.name || document.getElementById('name').value;
      document.getElementById('topology').value = r.payload.topology || document.getElementById('topology').value;
      document.getElementById('content').value = r.payload.content || document.getElementById('content').value;
      featureState = Array.isArray(r.payload.features) ? r.payload.features : featureState;
      pushHistory(getContentValue());
      runInfo();
    }
    show({ source: r.source, name: r.name, length: r.length, topology: r.topology, imported: true });
  } catch (e) { show(String(e)); }
}

async function runExportDna() {
  try {
    const r = await callApi('/api/export-dna', payload({}));
    document.getElementById('dnaBlob').value = r.dna_base64 || '';
    show({ format: r.format, name: r.name, length: r.length, bytes: r.bytes, exported: true });
  } catch (e) { show(String(e)); }
}

async function runImportAb1() {
  try {
    const ab1b64 = document.getElementById('ab1Base64').value.trim();
    const r = await callApi('/api/import-ab1', ab1b64 ? { ab1_base64: ab1b64 } : {
      sequence: plainSeq(document.getElementById('traceReference').value),
    });
    document.getElementById('traceId').value = r.trace_record?.trace_id || '';
    setInspectorText(
      `Trace imported\nTrace ID: ${r.trace_record?.trace_id || '-'}\n` +
      `Length: ${r.summary?.length || 0}\nQmean: ${r.summary?.quality_mean || 0}`
    );
    show(r.summary || r);
  } catch (e) { show(String(e)); }
}

async function runTraceSummary() {
  try {
    const trace_id = document.getElementById('traceId').value.trim();
    show(await callApi('/api/trace-summary', { trace_id }));
  } catch (e) { show(String(e)); }
}

async function runTraceAlign() {
  try {
    const trace_id = document.getElementById('traceId').value.trim();
    const reference_sequence = document.getElementById('traceReference').value;
    show(await callApi('/api/trace-align', { trace_id, reference_sequence }));
  } catch (e) { show(String(e)); }
}

async function runTraceEditBase() {
  try {
    const trace_id = document.getElementById('traceId').value.trim();
    show(await callApi('/api/trace-edit-base', {
      trace_id,
      position_1based: Number(document.getElementById('traceEditPos').value),
      new_base: document.getElementById('traceEditBase').value,
      quality: Number(document.getElementById('traceEditQual').value),
    }));
  } catch (e) { show(String(e)); }
}

async function runTraceConsensus() {
  try {
    const trace_id = document.getElementById('traceId').value.trim();
    show(await callApi('/api/trace-consensus', { trace_id, min_quality: 20 }));
  } catch (e) { show(String(e)); }
}

async function runTraceChromatogram() {
  try {
    const trace_id = document.getElementById('traceId').value.trim();
    const r = await callApi('/api/trace-chromatogram-svg', { trace_id, start: 1, end: 0, max_points: 400 });
    document.getElementById('traceChromViz').innerHTML = r.svg || '';
    enhancePanel('traceChromViz');
    show({ trace_id: r.trace_id, range: [r.start_1based, r.end_1based], points: r.points, max_signal: r.max_signal });
  } catch (e) { show(String(e)); }
}

async function runTraceVerify() {
  try {
    const trace_id = document.getElementById('traceId').value.trim();
    const reference_sequence = document.getElementById('traceReference').value;
    const genotype_positions = document.getElementById('traceGenotypePositions').value
      .split(',')
      .map((x) => Number(x.trim()))
      .filter((x) => Number.isFinite(x) && x > 0);
    let expected_bases = {};
    const raw = document.getElementById('traceExpectedBases').value.trim();
    if (raw) expected_bases = JSON.parse(raw);
    show(await callApi('/api/trace-verify', {
      trace_id,
      reference_sequence,
      min_quality: 20,
      genotype_positions,
      expected_bases,
      identity_threshold_pct: 98.0,
      max_mismatches: 5,
    }));
  } catch (e) { show(String(e)); }
}

function splitSeqLines(id) {
  return document.getElementById(id).value.split('\n').map((s) => s.trim()).filter(Boolean);
}

async function runPrimerSpecificity() {
  try {
    const backgrounds = splitSeqLines('primerSpecificityBackgrounds').map((sequence, i) => ({ name: `bg_${i+1}`, sequence }));
    show(await callApi('/api/primer-specificity', payload({
      forward: document.getElementById('forward').value,
      reverse: document.getElementById('reverse').value,
      background_sequences: backgrounds,
      max_mismatch: Number(document.getElementById('primerSpecificityMaxMm').value),
    })));
  } catch (e) { show(String(e)); }
}

async function runPrimerRank() {
  try {
    const candidates = JSON.parse(document.getElementById('primerRankCandidates').value);
    const backgrounds = splitSeqLines('primerSpecificityBackgrounds').map((sequence, i) => ({ name: `bg_${i+1}`, sequence }));
    show(await callApi('/api/primer-rank', {
      candidates,
      background_sequences: backgrounds,
      max_mismatch: Number(document.getElementById('primerSpecificityMaxMm').value),
    }));
  } catch (e) { show(String(e)); }
}

async function runGrnaDesign() {
  try {
    const r = await callApi('/api/grna-design', {
      sequence: plainSeq(document.getElementById('content').value) || plainSeq(document.getElementById('traceReference').value),
      pam: document.getElementById('crisprPam').value,
      spacer_len: Number(document.getElementById('crisprSpacerLen').value),
      max_candidates: Number(document.getElementById('crisprMaxCandidates').value),
    });
    if (Array.isArray(r.candidates) && r.candidates.length) {
      document.getElementById('crisprGuide').value = r.candidates[0].guide || '';
    }
    show(r);
  } catch (e) { show(String(e)); }
}

async function runCrisprOfftarget() {
  try {
    const backgrounds = splitSeqLines('primerSpecificityBackgrounds').map((sequence, i) => ({ name: `bg_${i+1}`, sequence }));
    show(await callApi('/api/crispr-offtarget', payload({
      guide: document.getElementById('crisprGuide').value,
      background_sequences: backgrounds,
      max_mismatch: 3,
    })));
  } catch (e) { show(String(e)); }
}

async function runHdrTemplate() {
  try {
    show(await callApi('/api/hdr-template', payload({
      sequence: plainSeq(document.getElementById('content').value),
      edit_start_1based: Number(document.getElementById('hdrEditStart').value),
      edit_end_1based: Number(document.getElementById('hdrEditEnd').value),
      edit_sequence: document.getElementById('hdrEditSeq').value,
      left_arm_bp: Number(document.getElementById('hdrLeftArm').value),
      right_arm_bp: Number(document.getElementById('hdrRightArm').value),
    })));
  } catch (e) { show(String(e)); }
}

