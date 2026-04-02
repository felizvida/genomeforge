// @ts-check
/* global callApi */

/** @typedef {{ key: string, location: string, qualifiers: Record<string, string> }} FeatureRecord */
/** @typedef {{ viewBox: string | null, startViewBox: string | null }} PanelViewport */

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
      listenersInstalled: false,
    };
    /** @type {Record<string, PanelViewport>} */
    const panelState = {};
    let selectedFeatureIndex = null;

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
      let dragging = false;
      let sx = 0;
      let sy = 0;
      svg.onwheel = (e) => {
        e.preventDefault();
        zoomPanel(panelId, e.deltaY < 0 ? 1.1 : 0.9);
      };
      svg.onmousedown = (e) => {
        dragging = true;
        sx = e.clientX;
        sy = e.clientY;
      };
      svg.onmouseup = () => { dragging = false; };
      svg.onmouseleave = () => { dragging = false; };
      svg.onmousemove = (e) => {
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
      };
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
    }

    function installMinimapDragListeners() {
      if (minimapState.listenersInstalled) return;
      window.addEventListener('mousemove', (ev) => {
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
      });
      window.addEventListener('mouseup', () => {
        if (!minimapState.dragging) return;
        resetMinimapDrag();
      });
      window.addEventListener('blur', () => {
        if (!minimapState.dragging) return;
        resetMinimapDrag();
      });
      minimapState.listenersInstalled = true;
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
      installMinimapDragListeners();

      brush.onmousedown = (ev) => {
        ev.preventDefault();
        minimapState.dragging = true;
        minimapState.mode = 'drag';
        const brushX = Number(brush.getAttribute('x'));
        const bpAtPointer = toBp(ev.clientX);
        const bpAtBrushLeft = 1 + Math.round(((brushX - x0) / trackW) * (len - 1));
        minimapState.dragOffsetBp = bpAtPointer - bpAtBrushLeft;
        minimapState.spanBp = Math.max(2, e - s + 1);
      };

      leftHandle.onmousedown = (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        minimapState.dragging = true;
        minimapState.mode = 'resize_left';
      };

      rightHandle.onmousedown = (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        minimapState.dragging = true;
        minimapState.mode = 'resize_right';
      };

      svg.onmousedown = (ev) => {
        if (ev.target === brush || ev.target === leftHandle || ev.target === rightHandle) return;
        const bp = toBp(ev.clientX);
        const span = Math.max(2, e - s + 1);
        setTrackWindow(bp - Math.floor(span / 2), bp + Math.ceil(span / 2));
      };
    }
