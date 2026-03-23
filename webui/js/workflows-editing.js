async function runFeatureList() {
  try {
    const r = await callApi('/api/features-list', payload());
    featureState = r.features || [];
    show(r);
  } catch (e) { show(String(e)); }
}

async function runFeatureAdd() {
  try {
    const key = document.getElementById('featKey').value;
    const location = document.getElementById('featLoc').value;
    const label = document.getElementById('featLabel').value;
    const r = await callApi('/api/features-add', payload({
      key,
      location,
      qualifiers: { label },
    }));
    featureState = r.features || [];
    show(r);
  } catch (e) { show(String(e)); }
}

async function runFeatureDelete() {
  try {
    const index = Number(document.getElementById('featIndex').value);
    const r = await callApi('/api/features-delete', payload({ index }));
    featureState = r.features || [];
    show(r);
  } catch (e) { show(String(e)); }
}

function editBody() {
  return payload({
    op: document.getElementById('editOp').value,
    start: Number(document.getElementById('editStart').value),
    end: Number(document.getElementById('editEnd').value),
    value: document.getElementById('editValue').value,
  });
}

async function previewEdit() {
  try {
    const r = await callApi('/api/sequence-edit', editBody());
    show({ preview_length: r.length, preview_gc: r.gc, preview_sequence_head: r.sequence.slice(0, 120) });
  } catch (e) { show(String(e)); }
}

async function applyEditToBuffer() {
  try {
    const r = await callApi('/api/sequence-edit', editBody());
    document.getElementById('content').value = `>${r.name}\n${r.sequence}`;
    pushHistory(getContentValue());
    setStats(r);
    show({ applied: true, length: r.length, gc: r.gc });
  } catch (e) { show(String(e)); }
}

