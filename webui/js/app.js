// @ts-check
/* global runMap, runDigest, runSequenceTrack, runPrimerDesign, runCodonOptimize, runMSA, runProjectSave, runProjectLoad, pushHistory, getContentValue, renderTrackMiniMap, refreshLigationGraph, activateTab, runInfo, setInspectorText */

function activateTab(tabId) {
  document.querySelectorAll('#tabs .tab').forEach((tab) => {
    tab.classList.toggle('active', tab.dataset.tab === tabId);
  });
  document.querySelectorAll('.tabpane').forEach((pane) => {
    pane.classList.toggle('active', pane.id === tabId);
  });
}

document.getElementById('tabs').addEventListener('click', (e) => {
  const btn = e.target.closest('.tab');
  if (!btn) return;
  activateTab(btn.dataset.tab);
});

function parseActionArgs(btn) {
  const rawArgs = btn.getAttribute('data-args');
  if (!rawArgs) return [];
  try {
    const parsed = JSON.parse(rawArgs);
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch (_) {
    return [];
  }
}

document.addEventListener('click', async (e) => {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;
  const action = btn.getAttribute('data-action');
  if (!action || typeof window[action] !== 'function') return;
  e.preventDefault();
  try {
    await window[action](...parseActionArgs(btn));
  } catch (_) {}
});

window.addEventListener('keydown', async (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    const cmd = (window.prompt('Quick command: map, digest, track, primers, optimize, msa, save, load', 'map') || '')
      .trim()
      .toLowerCase();
    const commandMap = {
      map: () => runMap(),
      digest: () => runDigest(),
      track: () => runSequenceTrack(),
      primers: () => runPrimerDesign(),
      optimize: () => runCodonOptimize(),
      msa: () => runMSA(),
      save: () => runProjectSave(),
      load: () => runProjectLoad(),
    };
    if (commandMap[cmd]) {
      await commandMap[cmd]();
    } else if (cmd) {
      setInspectorText(`Unknown quick command: ${cmd}`);
    }
  }
});

document.getElementById('content').addEventListener('change', () => pushHistory(getContentValue()));
document.getElementById('trackStart').addEventListener('input', () => renderTrackMiniMap());
document.getElementById('trackEnd').addEventListener('input', () => renderTrackMiniMap());
document.getElementById('ligGraphFilter').addEventListener('change', () => refreshLigationGraph());

try {
  const stack = JSON.parse(localStorage.getItem('genomeforge_history_stack') || '[]');
  const idx = Number(localStorage.getItem('genomeforge_history_index') || -1);
  if (Array.isArray(stack) && stack.length && idx >= 0 && idx < stack.length) {
    historyState.stack = stack.map((x) => String(x));
    historyState.index = idx;
    document.getElementById('content').value = historyState.stack[idx];
  } else {
    pushHistory(getContentValue());
  }
} catch (_) {
  pushHistory(getContentValue());
}

runInfo();
