// @ts-check
/* global callApi */

/** @typedef {{ key: string, location: string, qualifiers: Record<string, string> }} FeatureRecord */
/** @typedef {{ viewBox: string | null, startViewBox: string | null, panZoomController?: AbortController | null }} PanelViewport */

    const historyState = {
      stack: [],
      index: -1,
    };
    /** @type {FeatureRecord[]} */
    let featureState = [];
    let lastMSAAlignment = [];
    let lastLigationResult = null;
    const minimapState = {
      dragging: false,
      dragOffsetBp: 0,
      mode: '',
      spanBp: 0,
      context: null,
      dragController: null,
    };
    /** @type {Record<string, PanelViewport>} */
    const panelState = {};
    let selectedFeatureIndex = null;
    const learningState = {
      active: false,
      scenarioId: 'plasmid-map',
      stepIndex: 0,
      highlighted: null,
    };
    const learningScenarios = {
      'plasmid-map': {
        title: 'Plasmid map and unique cutters',
        concept: 'A plasmid map is a physical experiment plan: topology, features, and restriction sites tell you how the molecule can be cut and verified.',
        expected: 'Map Preview shows a circular/linear map and the inspector can identify features or cuts.',
        decision: 'Choose cutters only if they are unique, interpretable, and compatible with the cloning question.',
        steps: [
          { tab: 'tab-map', target: '#content', text: 'Load a pUC19 or tutorial bundle FASTA here. Confirm this is the record you intend to map.' },
          { tab: 'tab-map', target: '#enzymes', text: 'Use a small enzyme set first, such as EcoRI,BamHI,HindIII, before expanding the search.' },
          { tab: 'tab-map', target: 'button[data-action="runMap"]', text: 'Render the map, then click a cut or feature to inspect why it matters.' },
          { tab: 'tab-map', target: '#map', text: 'Interpret the map as a wet-lab plan, not a decorative diagram.' },
        ],
      },
      'text-map': {
        title: 'Text map as source-code view',
        concept: 'Text maps align sequence, coordinates, translation, and feature annotations in a compact source-code-like view.',
        expected: 'Text Map displays coordinate blocks, DNA rows, translation context, and feature labels.',
        decision: 'Use the text map when a graphic map is too zoomed out for codon-level reasoning.',
        steps: [
          { tab: 'tab-map', target: '#trackStart', text: 'Choose a narrow window so the text view remains readable.' },
          { tab: 'tab-map', target: '#trackFrame', text: 'Set the frame before interpreting amino acids.' },
          { tab: 'tab-map', target: '#textMapWidth', text: 'Start with width 80; wider text can be harder to print or compare.' },
          { tab: 'tab-map', target: 'button[data-action="runTextMap"]', text: 'Render the text map and read bases, codons, and annotations together.' },
        ],
      },
      'diagnostic-digest': {
        title: 'Diagnostic digest between constructs',
        concept: 'A diagnostic digest turns an invisible sequence difference into visible gel-band evidence.',
        expected: 'Diagnostic Restriction View lists enzymes whose cut counts differ between the two sequences.',
        decision: 'Pick the cutter that answers the discrimination question with a readable band pattern.',
        steps: [
          { tab: 'tab-advanced', target: '#restrictionCompareSeq', text: 'Paste the related construct or allele you want to compare against the current record.' },
          { tab: 'tab-map', target: '#enzymes', text: 'Set the enzyme panel. Good diagnostic cutters are often found by trying a focused panel first.' },
          { tab: 'tab-advanced', target: '#restrictionMinDelta', text: 'Use minimum delta 1 when searching for one-site differences.' },
          { tab: 'tab-advanced', target: 'button[data-action="runRestrictionCompare"]', text: 'Run the comparison and inspect which enzyme cuts one sequence more often than the other.' },
        ],
      },
      'custom-ladder': {
        title: 'Custom ladder digest planning',
        concept: 'A DNA ladder is the visual ruler for an agarose gel; in-house ladders change what fragment differences are readable.',
        expected: 'Digest output is interpreted against the custom ladder sizes saved in the UI.',
        decision: 'Use a custom ladder when the simulated output should match the marker actually used at the bench.',
        steps: [
          { tab: 'tab-advanced', target: '#gelLadderName', text: 'Name the in-house ladder so it can be reused in digest planning.' },
          { tab: 'tab-advanced', target: '#gelLadderSizes', text: 'Enter ladder sizes from large to small, comma-separated.' },
          { tab: 'tab-advanced', target: 'button[data-action="runGelLadderSave"]', text: 'Save the ladder before using it as a digest marker.' },
          { tab: 'tab-advanced', target: 'button[data-action="runDigestGel"]', text: 'Run the digest gel and decide whether the expected bands are actually readable.' },
        ],
      },
      'silent-site': {
        title: 'Silent restriction-site engineering',
        concept: 'Genetic-code degeneracy lets some DNA edits preserve the protein while adding or removing a useful restriction site.',
        expected: 'Silent Restriction Site View lists enzyme sites, codon swaps, and base edits that preserve amino acid identity.',
        decision: 'Accept only candidates that preserve translation and do not create new downstream risks.',
        steps: [
          { tab: 'tab-analysis', target: '#frame', text: 'Set the coding frame; silent-site logic is meaningless in the wrong frame.' },
          { tab: 'tab-map', target: '#enzymes', text: 'Choose the enzyme set you want to introduce or evaluate.' },
          { tab: 'tab-advanced', target: '#silentMaxCandidates', text: 'Keep the candidate limit modest while learning; inspect quality rather than volume.' },
          { tab: 'tab-advanced', target: 'button[data-action="runSilentRestrictionSites"]', text: 'Run the search and click a candidate to inspect its sequence context.' },
        ],
      },
      'trace-review': {
        title: 'Chromatogram-first trace review',
        concept: 'Sanger base calls are inferred from peak evidence, so the chromatogram must be reviewed before accepting a construct.',
        expected: 'Sanger Chromatogram shows peak evidence for the selected trace window.',
        decision: 'Accept sequence calls only where peaks support them; repeat weak or mixed regions.',
        steps: [
          { tab: 'tab-trace', target: '#ab1Base64', text: 'Import or paste trace evidence. The called letters are not the whole experiment.' },
          { tab: 'tab-trace', target: '#traceId', text: 'Confirm the trace ID before running downstream trace actions.' },
          { tab: 'tab-trace', target: 'button[data-action="runTraceChromatogram"]', text: 'Render the chromatogram and inspect peak quality before interpreting mismatches.' },
          { tab: 'tab-trace', target: '#traceChromViz', text: 'Look for clean isolated peaks, mixed peaks, and low-confidence edges.' },
        ],
      },
      'trace-links': {
        title: 'Linked trace-to-reference navigation',
        concept: 'Linked trace navigation turns a mismatch row into a route back to raw evidence and reference context.',
        expected: 'Trace-to-Reference Links provides clickable evidence rows or local mismatch context.',
        decision: 'Use links to challenge automatic calls, especially around decision-critical bases.',
        steps: [
          { tab: 'tab-trace', target: '#traceReference', text: 'Paste the intended reference sequence in the correct orientation.' },
          { tab: 'tab-trace', target: '#traceWindowStart', text: 'Set a narrow window around the mismatch or verification region.' },
          { tab: 'tab-trace', target: 'button[data-action="runTraceAlignmentLinks"]', text: 'Generate linked alignment rows and inspect the trace evidence behind each call.' },
          { tab: 'tab-trace', target: '#traceLinkViz', text: 'Use the links as evidence navigation, not as a substitute for interpretation.' },
        ],
      },
      'blast-launch': {
        title: 'Selected-sequence BLAST handoff',
        concept: 'BLAST launch is a precise handoff from local sequence context to public-reference search.',
        expected: 'External BLAST Launchpad shows provider-specific launch links and a copyable FASTA query.',
        decision: 'Interpret public hits with query coordinates, coverage, and database scope in mind.',
        steps: [
          { tab: 'tab-advanced', target: '#blastQuery', text: 'Paste the selected region, or leave blank to use the current record.' },
          { tab: 'tab-advanced', target: '#blastProvider', text: 'Choose NCBI for broad nucleotide search or WormBase for organism-specific follow-up.' },
          { tab: 'tab-advanced', target: '#blastDatabase', text: 'Confirm the database; database scope changes what a top hit means.' },
          { tab: 'tab-advanced', target: 'button[data-action="runBlastLaunch"]', text: 'Launch or copy the query, then record provider, coordinates, and interpretation.' },
        ],
      },
      'project-handoff': {
        title: 'Reproducible project handoff',
        concept: 'A scientific result is more trustworthy when the molecule, evidence, parameters, and review trail travel together.',
        expected: 'Saved project/share/history output can be reopened by another person or browser session.',
        decision: 'Handoff only when the next scientist can recover data, reasoning, and limitations without your memory.',
        steps: [
          { tab: 'tab-advanced', target: '#projectName', text: 'Use a project name that describes the molecule and decision state.' },
          { tab: 'tab-advanced', target: 'button[data-action="runProjectSave"]', text: 'Save project state before creating share or review artifacts.' },
          { tab: 'tab-advanced', target: 'button[data-action="runShareCreate"]', text: 'Create a share bundle for a clean handoff.' },
          { tab: 'tab-advanced', target: '#historyGraph', text: 'Inspect history so the reasoning trail remains attached to the sequence.' },
        ],
      },
    };

    function payload(extra = {}) {
      return {
        name: document.getElementById('name').value,
        topology: document.getElementById('topology').value,
        content: document.getElementById('content').value,
        features: featureState,
        ...extra,
      };
    }

    function show(data) {
      document.getElementById('out').textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
    }

    function escapeHtml(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function clearLearningHighlight() {
      if (learningState.highlighted) {
        learningState.highlighted.classList.remove('learning-highlight');
        learningState.highlighted = null;
      }
    }

    function highlightLearningTarget(selector) {
      clearLearningHighlight();
      const target = document.querySelector(selector);
      if (!target) return;
      target.classList.add('learning-highlight');
      learningState.highlighted = target;
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function renderDecisionCard(card) {
      const host = document.getElementById('decisionCardViz');
      if (!host || !card) return;
      host.innerHTML = `
        <h3>${escapeHtml(card.title || 'Evidence-to-Decision')}</h3>
        <p><b>Evidence:</b> ${escapeHtml(card.evidence || 'Run a workflow to collect evidence.')}</p>
        <p><b>Inference:</b> ${escapeHtml(card.inference || 'Interpret the evidence in biological context.')}</p>
        <p><b>Confidence limit:</b> ${escapeHtml(card.limit || 'Check input type, parameters, and evidence quality before acting.')}</p>
        <p><b>Next bench action:</b> ${escapeHtml(card.next || 'Choose the next experiment or review step explicitly.')}</p>
      `;
    }

    function setDecisionCard(kind, result = {}, extra = {}) {
      const defaults = {
        generic: {
          title: 'Evidence-to-Decision',
          evidence: 'Workflow output is available in Results.',
          inference: 'The output needs a biological interpretation before it becomes a conclusion.',
          limit: 'Confidence depends on the input record, parameters, and evidence quality.',
          next: 'Write a one-sentence decision before changing the molecule or reporting the result.',
        },
        map: {
          title: 'Map Evidence-to-Decision',
          evidence: 'Map and restriction features are visible in the current molecule context.',
          inference: 'Cuts and features define what cloning or verification moves are physically plausible.',
          limit: 'A map is only as trustworthy as its sequence, topology, and annotation source.',
          next: 'Choose a unique, interpretable cut or verify the relevant feature before cloning.',
        },
        text_map: {
          title: 'Text Map Evidence-to-Decision',
          evidence: 'Coordinates, DNA text, translation, and features are aligned in one view.',
          inference: 'Local edits can be interpreted at base, codon, and feature levels together.',
          limit: 'Translation meaning depends on the selected frame and biological object type.',
          next: 'Use the text view to justify the exact coordinate or codon you plan to edit or report.',
        },
        diagnostic_digest: {
          title: 'Diagnostic Digest Evidence-to-Decision',
          evidence: `${result.diagnostic_count ?? 0} discriminatory candidate(s) found between the two sequences.`,
          inference: 'A useful cutter converts a sequence difference into a readable gel difference.',
          limit: 'Cut-count difference is not enough; fragment sizes must also be resolvable.',
          next: 'Pick one enzyme and write the expected parent/variant band pattern before running the digest.',
        },
        custom_ladder: {
          title: 'Custom Ladder Evidence-to-Decision',
          evidence: 'Digest fragments are being evaluated against the selected lab ladder.',
          inference: 'Readability depends on marker spacing as much as on correct cutting chemistry.',
          limit: 'A correct digest can still be experimentally ambiguous if bands are too close.',
          next: 'Use the ladder that matches the bench gel and revise enzyme choice if bands are not separable.',
        },
        silent_site: {
          title: 'Silent Site Evidence-to-Decision',
          evidence: `${result.candidate_count ?? 0} protein-preserving restriction-site candidate(s) reported.`,
          inference: 'Synonymous edits can add a screening handle while preserving amino acid identity.',
          limit: 'Silent does not guarantee neutral; codon usage, RNA context, and feature overlap can still matter.',
          next: 'Verify translation and inspect local context before accepting the engineered site.',
        },
        trace: {
          title: 'Trace Evidence-to-Decision',
          evidence: 'Trace output links called sequence back to chromatogram or alignment evidence.',
          inference: 'Construct or genotype calls are defensible only where raw peaks support the base call.',
          limit: 'Weak, mixed, or edge peaks require caution even when the consensus looks clean.',
          next: 'Accept, repeat, or add opposite-strand evidence based on the weakest decision-critical region.',
        },
        blast: {
          title: 'BLAST Handoff Evidence-to-Decision',
          evidence: 'A coordinate-aware query is ready for NCBI or WormBase follow-up.',
          inference: 'Public hits can support identity or contamination hypotheses when interpreted with coverage and scope.',
          limit: 'The top hit is not proof without query length, coverage, and database context.',
          next: 'Record provider, query coordinates, top-hit coverage, and any contamination hypothesis.',
        },
        project: {
          title: 'Reproducibility Evidence-to-Decision',
          evidence: 'Project/share/history output preserves sequence state and workflow context.',
          inference: 'The work is handoff-ready only if another scientist can reopen and interrogate it.',
          limit: 'Screenshots alone are not reproducible scientific state.',
          next: 'Reload the saved artifact in a clean session and document remaining limitations.',
        },
      };
      renderDecisionCard({ ...(defaults[kind] || defaults.generic), ...extra });
    }

    function activeLearningScenario() {
      return learningScenarios[learningState.scenarioId] || learningScenarios['plasmid-map'];
    }

    function renderLearningStep() {
      const panel = document.getElementById('learningModePanel');
      const stepHost = document.getElementById('learningStepCard');
      const progress = document.getElementById('learningProgress');
      if (!panel || !stepHost || !progress) return;
      const scenario = activeLearningScenario();
      const step = scenario.steps[Math.max(0, Math.min(learningState.stepIndex, scenario.steps.length - 1))];
      learningState.stepIndex = scenario.steps.indexOf(step);
      if (step.tab && typeof activateTab === 'function') activateTab(step.tab);
      progress.textContent = `${learningState.stepIndex + 1}/${scenario.steps.length}`;
      stepHost.innerHTML = `
        <b>${escapeHtml(scenario.title)}</b>
        <p>${escapeHtml(step.text)}</p>
        <p><span>Concept:</span> ${escapeHtml(scenario.concept)}</p>
        <p><span>Expected result:</span> ${escapeHtml(scenario.expected)}</p>
        <p><span>Decision prompt:</span> ${escapeHtml(scenario.decision)}</p>
      `;
      highlightLearningTarget(step.target);
      renderDecisionCard({
        title: `Learning Mode: ${scenario.title}`,
        evidence: scenario.expected,
        inference: scenario.concept,
        limit: 'This guided step teaches interpretation; still verify your loaded sequence, parameters, and sample data.',
        next: scenario.decision,
      });
    }

    function toggleLearningMode() {
      const panel = document.getElementById('learningModePanel');
      if (!panel) return;
      learningState.active = panel.hidden;
      panel.hidden = !learningState.active;
      if (learningState.active) {
        const select = document.getElementById('learningScenario');
        if (select) learningState.scenarioId = select.value;
        renderLearningStep();
      } else {
        clearLearningHighlight();
      }
    }

    function startLearningScenario() {
      const panel = document.getElementById('learningModePanel');
      const select = document.getElementById('learningScenario');
      if (!panel || !select) return;
      learningState.active = true;
      learningState.scenarioId = select.value;
      learningState.stepIndex = 0;
      panel.hidden = false;
      renderLearningStep();
    }

    function nextLearningStep() {
      const scenario = activeLearningScenario();
      learningState.stepIndex = Math.min(scenario.steps.length - 1, learningState.stepIndex + 1);
      renderLearningStep();
    }

    function previousLearningStep() {
      learningState.stepIndex = Math.max(0, learningState.stepIndex - 1);
      renderLearningStep();
    }

    function panelSvg(panelId) {
      return document.querySelector(`#${panelId} svg`);
    }

    function ensurePanelState(panelId) {
      if (!panelState[panelId]) panelState[panelId] = { viewBox: null, startViewBox: null };
      return panelState[panelId];
    }

    function attachPanZoom(panelId) {
      const svg = panelSvg(panelId);
      if (!svg) return;
      const state = ensurePanelState(panelId);
      if (!svg.hasAttribute('viewBox')) {
        const w = Number(svg.getAttribute('width')) || svg.clientWidth || 1000;
        const h = Number(svg.getAttribute('height')) || svg.clientHeight || 600;
        svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
      }
      if (!state.viewBox) state.viewBox = svg.getAttribute('viewBox');
      state.startViewBox = state.viewBox;
      svg.setAttribute('viewBox', state.viewBox);
      if (state.panZoomController) state.panZoomController.abort();
      state.panZoomController = new AbortController();
      const { signal } = state.panZoomController;
      svg.style.touchAction = 'none';
      let dragging = false;
      let sx = 0;
      let sy = 0;
      svg.addEventListener('wheel', (e) => {
        e.preventDefault();
        zoomPanel(panelId, e.deltaY < 0 ? 1.1 : 0.9);
      }, { signal, passive: false });
      svg.addEventListener('pointerdown', (e) => {
        if (e.target.closest('[data-feature-index], [data-cut-enzyme], [data-codon-start]')) return;
        dragging = true;
        sx = e.clientX;
        sy = e.clientY;
        try {
          svg.setPointerCapture(e.pointerId);
        } catch {
          // Pointer capture can fail if the element is detached during a redraw.
        }
      }, { signal });
      const endDrag = (e) => {
        dragging = false;
        if (e?.pointerId !== undefined) {
          try {
            svg.releasePointerCapture(e.pointerId);
          } catch {
            // Safe to ignore when capture was already released.
          }
        }
      };
      svg.addEventListener('pointerup', endDrag, { signal });
      svg.addEventListener('pointercancel', endDrag, { signal });
      svg.addEventListener('lostpointercapture', endDrag, { signal });
      svg.addEventListener('pointermove', (e) => {
        if (!dragging) return;
        const vb = (panelState[panelId]?.viewBox || svg.getAttribute('viewBox')).split(/\s+/).map(Number);
        const scaleX = vb[2] / Math.max(svg.clientWidth, 1);
        const scaleY = vb[3] / Math.max(svg.clientHeight, 1);
        const dx = (e.clientX - sx) * scaleX;
        const dy = (e.clientY - sy) * scaleY;
        vb[0] -= dx;
        vb[1] -= dy;
        panelState[panelId].viewBox = vb.join(' ');
        svg.setAttribute('viewBox', panelState[panelId].viewBox);
        sx = e.clientX;
        sy = e.clientY;
      }, { signal });
    }

    function zoomPanel(panelId, factor) {
      const svg = panelSvg(panelId);
      if (!svg) return;
      const st = ensurePanelState(panelId);
      const vb = (st.viewBox || svg.getAttribute('viewBox')).split(/\s+/).map(Number);
      const cx = vb[0] + vb[2] / 2;
      const cy = vb[1] + vb[3] / 2;
      vb[2] /= factor;
      vb[3] /= factor;
      vb[0] = cx - vb[2] / 2;
      vb[1] = cy - vb[3] / 2;
      st.viewBox = vb.join(' ');
      svg.setAttribute('viewBox', st.viewBox);
    }

    function resetPanelView(panelId) {
      const svg = panelSvg(panelId);
      const st = panelState[panelId];
      if (!svg || !st || !st.startViewBox) return;
      st.viewBox = st.startViewBox;
      svg.setAttribute('viewBox', st.viewBox);
    }

    function setInspectorText(text) {
      document.getElementById('inspector').textContent = text;
    }

    function selectFeature(idx) {
      selectedFeatureIndex = Number(idx);
      document.querySelectorAll('#map [data-feature-index], #seqTrack [data-feature-index]').forEach((el) => {
        if (Number(el.getAttribute('data-feature-index')) === selectedFeatureIndex) {
          el.classList.add('selected-feature');
        } else {
          el.classList.remove('selected-feature');
        }
      });
      const f = featureState[selectedFeatureIndex];
      if (!f) {
        setInspectorText(`Feature ${selectedFeatureIndex}: not loaded in current feature state.`);
        return;
      }
      const label = (f.qualifiers && (f.qualifiers.label || f.qualifiers.gene || f.qualifiers.product)) || f.key || 'feature';
      setInspectorText(
        `Feature #${selectedFeatureIndex}\n` +
        `Label: ${label}\n` +
        `Type: ${f.key || 'misc_feature'}\n` +
        `Location: ${f.location || '-'}`
      );
    }

    function bindPanelSelection(panelId) {
      const host = document.getElementById(panelId);
      host.onclick = (e) => {
        const t = e.target.closest('[data-feature-index], [data-cut-enzyme], [data-codon-start]');
        if (!t) return;
        if (t.hasAttribute('data-feature-index')) {
          selectFeature(t.getAttribute('data-feature-index'));
          return;
        }
        if (t.hasAttribute('data-cut-enzyme')) {
          const enz = t.getAttribute('data-cut-enzyme');
          const pos = t.getAttribute('data-cut-position');
          setInspectorText(`Restriction cut\nEnzyme: ${enz}\nPosition: ${pos}`);
          return;
        }
        if (t.hasAttribute('data-codon-start')) {
          setInspectorText(
            `Translation cell\nCodon: ${t.getAttribute('data-codon-start')}..${t.getAttribute('data-codon-end')}\n` +
            `Residue: ${t.getAttribute('data-residue')}`
          );
        }
      };
    }

    function enhancePanel(panelId) {
      attachPanZoom(panelId);
      bindPanelSelection(panelId);
      if (selectedFeatureIndex !== null) selectFeature(selectedFeatureIndex);
    }

    function getContentValue() {
      return document.getElementById('content').value;
    }

    function plainSeq(text) {
      return String(text || '').toUpperCase().replace(/[^ACGTRYSWKMBDHVN]/g, '');
    }

    function setContentValue(v) {
      document.getElementById('content').value = v;
    }

    function pushHistory(v) {
      const value = String(v ?? '');
      if (historyState.index >= 0 && historyState.stack[historyState.index] === value) return;
      historyState.stack = historyState.stack.slice(0, historyState.index + 1);
      historyState.stack.push(value);
      historyState.index = historyState.stack.length - 1;
      if (historyState.stack.length > 200) {
        historyState.stack.shift();
        historyState.index -= 1;
      }
      try {
        localStorage.setItem('genomeforge_history_stack', JSON.stringify(historyState.stack));
        localStorage.setItem('genomeforge_history_index', String(historyState.index));
      } catch (_) {}
    }

    function undoSequence() {
      if (historyState.index <= 0) return;
      historyState.index -= 1;
      setContentValue(historyState.stack[historyState.index]);
      runInfo();
    }

    function redoSequence() {
      if (historyState.index >= historyState.stack.length - 1) return;
      historyState.index += 1;
      setContentValue(historyState.stack[historyState.index]);
      runInfo();
    }

    function setStats(info) {
      if (!info) return;
      document.getElementById('sName').textContent = info.name || '-';
      document.getElementById('sLen').textContent = info.length ?? '-';
      document.getElementById('sGc').textContent = (info.gc ?? '-') + '';
      document.getElementById('sTopo').textContent = info.topology || '-';
      renderTrackMiniMap();
    }

    function currentSeqLength() {
      return Number(document.getElementById('sLen').textContent) || 0;
    }

    function clampWindow(start, end, len) {
      if (len <= 0) return [1, Math.max(1, end)];
      let s = Math.max(1, Math.min(start, len));
      let e = Math.max(s, Math.min(end, len));
      if (e === s) e = Math.min(len, s + 1);
      return [s, e];
    }

    function trackWindow() {
      const len = currentSeqLength();
      const start = Number(document.getElementById('trackStart').value) || 1;
      const end = Number(document.getElementById('trackEnd').value) || Math.min(len || 120, 120);
      return clampWindow(start, end, len || Math.max(120, end));
    }

    function setTrackWindow(start, end) {
      const len = currentSeqLength();
      const [s, e] = clampWindow(start, end, len || Math.max(end, 120));
      document.getElementById('trackStart').value = s;
      document.getElementById('trackEnd').value = e;
      renderTrackMiniMap();
    }

    function shiftTrackWindow(fraction) {
      const len = currentSeqLength();
      if (len <= 0) return;
      const [s, e] = trackWindow();
      const w = Math.max(2, e - s);
      const delta = Math.round(w * fraction);
      setTrackWindow(s + delta, e + delta);
    }

    function setFullTrackWindow() {
      const len = currentSeqLength();
      if (len <= 0) return;
      setTrackWindow(1, len);
    }

    function parseFeatureBounds(location) {
      const nums = String(location || '').match(/\d+/g) || [];
      if (nums.length < 2) return null;
      let a = Number(nums[0]);
      let b = Number(nums[nums.length - 1]);
      if (!a || !b) return null;
      if (a > b) [a, b] = [b, a];
      return [a, b];
    }

    function resetMinimapDrag() {
      minimapState.dragging = false;
      minimapState.mode = '';
      minimapState.dragOffsetBp = 0;
      minimapState.spanBp = 0;
      if (minimapState.dragController) {
        minimapState.dragController.abort();
        minimapState.dragController = null;
      }
    }

    function updateMinimapDrag(ev) {
      if (!minimapState.dragging || !minimapState.context) return;
      const { toBp } = minimapState.context;
      const [curS, curE] = trackWindow();
      if (minimapState.mode === 'drag') {
        const span = Math.max(2, minimapState.spanBp || (curE - curS + 1));
        const leftBp = toBp(ev.clientX) - minimapState.dragOffsetBp;
        setTrackWindow(leftBp, leftBp + span - 1);
      } else if (minimapState.mode === 'resize_left') {
        setTrackWindow(toBp(ev.clientX), curE);
      } else if (minimapState.mode === 'resize_right') {
        setTrackWindow(curS, toBp(ev.clientX));
      }
    }

    function startMinimapDrag(mode, ev) {
      ev.preventDefault();
      resetMinimapDrag();
      minimapState.dragging = true;
      minimapState.mode = mode;
      minimapState.dragController = new AbortController();
      const { signal } = minimapState.dragController;
      window.addEventListener('pointermove', updateMinimapDrag, { signal });
      window.addEventListener('pointerup', resetMinimapDrag, { signal });
      window.addEventListener('pointercancel', resetMinimapDrag, { signal });
      window.addEventListener('blur', resetMinimapDrag, { signal });
    }

    function renderTrackMiniMap() {
      const host = document.getElementById('trackMiniMap');
      const len = currentSeqLength();
      if (len <= 0) {
        minimapState.context = null;
        resetMinimapDrag();
        host.textContent = 'Track minimap appears after sequence info loads.';
        return;
      }
      const [s, e] = trackWindow();
      const w = 980;
      const h = 92;
      const x0 = 24;
      const trackW = w - x0 * 2;
      const y = 44;
      const windowX = x0 + ((s - 1) / len) * trackW;
      const windowW = Math.max(4, ((e - s + 1) / len) * trackW);

      const featureRects = (featureState || []).map((f, idx) => {
        const b = parseFeatureBounds(f.location);
        if (!b) return '';
        const a = b[0];
        const z = b[1];
        const fx = x0 + ((a - 1) / len) * trackW;
        const fw = Math.max(1, ((z - a + 1) / len) * trackW);
        const color = idx === selectedFeatureIndex ? '#f43f5e' : '#0ea5e9';
        return `<rect x="${fx.toFixed(2)}" y="${(y-10).toFixed(2)}" width="${fw.toFixed(2)}" height="6" rx="3" fill="${color}" opacity="0.9"></rect>`;
      }).join('');

      host.innerHTML = `
        <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
          <rect x="0" y="0" width="${w}" height="${h}" fill="#f8fafc"></rect>
          <rect x="${x0}" y="${y}" width="${trackW}" height="8" rx="4" fill="#e2e8f0"></rect>
          ${featureRects}
          <rect id="miniBrush" x="${windowX.toFixed(2)}" y="${(y-8).toFixed(2)}" width="${windowW.toFixed(2)}" height="24" rx="6" fill="rgba(15,118,110,0.2)" stroke="#0f766e" stroke-width="2"></rect>
          <rect id="miniHandleLeft" x="${(windowX - 2).toFixed(2)}" y="${(y-10).toFixed(2)}" width="5" height="28" rx="2" fill="#0f766e"></rect>
          <rect id="miniHandleRight" x="${(windowX + windowW - 3).toFixed(2)}" y="${(y-10).toFixed(2)}" width="5" height="28" rx="2" fill="#0f766e"></rect>
          <text x="${x0}" y="20" font-size="11" font-family="Menlo, monospace" fill="#334155">1</text>
          <text x="${w-x0}" y="20" text-anchor="end" font-size="11" font-family="Menlo, monospace" fill="#334155">${len}</text>
          <text x="${w/2}" y="20" text-anchor="middle" font-size="11" font-family="Menlo, monospace" fill="#0f172a">Window ${s}..${e} (${e - s + 1} bp)</text>
        </svg>
      `;

      const svg = host.querySelector('svg');
      const brush = host.querySelector('#miniBrush');
      const leftHandle = host.querySelector('#miniHandleLeft');
      const rightHandle = host.querySelector('#miniHandleRight');
      if (!svg || !brush || !leftHandle || !rightHandle) return;
      const toBp = (clientX) => {
        const rect = svg.getBoundingClientRect();
        const px = ((clientX - rect.left) / Math.max(rect.width, 1)) * w;
        const frac = Math.max(0, Math.min(1, (px - x0) / trackW));
        return 1 + Math.round(frac * (len - 1));
      };
      minimapState.context = { toBp };

      brush.addEventListener('pointerdown', (ev) => {
        startMinimapDrag('drag', ev);
        const brushX = Number(brush.getAttribute('x'));
        const bpAtPointer = toBp(ev.clientX);
        const bpAtBrushLeft = 1 + Math.round(((brushX - x0) / trackW) * (len - 1));
        minimapState.dragOffsetBp = bpAtPointer - bpAtBrushLeft;
        minimapState.spanBp = Math.max(2, e - s + 1);
      });

      leftHandle.addEventListener('pointerdown', (ev) => {
        ev.stopPropagation();
        startMinimapDrag('resize_left', ev);
      });

      rightHandle.addEventListener('pointerdown', (ev) => {
        ev.stopPropagation();
        startMinimapDrag('resize_right', ev);
      });

      svg.addEventListener('pointerdown', (ev) => {
        if (ev.target === brush || ev.target === leftHandle || ev.target === rightHandle) return;
        const bp = toBp(ev.clientX);
        const span = Math.max(2, e - s + 1);
        setTrackWindow(bp - Math.floor(span / 2), bp + Math.ceil(span / 2));
      });
    }
