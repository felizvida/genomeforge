async function runGibsonAssemble() {
  try {
    const fragments = JSON.parse(document.getElementById('gibsonFrags').value);
    show(await callApi('/api/gibson-assemble', {
      fragments,
      min_overlap: Number(document.getElementById('gibsonOverlap').value),
      circular: false,
    }));
  } catch (e) { show(String(e)); }
}

async function runGoldenGateAssemble() {
  try {
    const parts = JSON.parse(document.getElementById('goldenParts').value);
    show(await callApi('/api/golden-gate', {
      parts,
      circular: true,
      enforce_complement: true,
    }));
  } catch (e) { show(String(e)); }
}


async function runGatewayCloning() {
  try {
    show(await callApi('/api/gateway-cloning', {
      entry_clone: document.getElementById('entryClone').value,
      destination_vector: document.getElementById('destVector').value,
    }));
  } catch (e) { show(String(e)); }
}

async function runTopoCloning() {
  try {
    show(await callApi('/api/topo-cloning', {
      vector: document.getElementById('destVector').value,
      insert: document.getElementById('entryClone').value,
      mode: document.getElementById('cloneMode').value === 'BLUNT' ? 'BLUNT' : 'TA',
    }));
  } catch (e) { show(String(e)); }
}

async function runTAGCCloning() {
  try {
    const mode = document.getElementById('cloneMode').value === 'GC' ? 'GC' : 'TA';
    show(await callApi('/api/ta-gc-cloning', {
      vector: document.getElementById('destVector').value,
      insert: document.getElementById('entryClone').value,
      mode,
    }));
  } catch (e) { show(String(e)); }
}

async function runCloningCompatibility() {
  try {
    show(await callApi('/api/cloning-compatibility', {
      mode: document.getElementById('compatMode').value,
      vector: document.getElementById('destVector').value,
      insert: document.getElementById('entryClone').value,
      enzymes: document.getElementById('enzymes').value,
      left_overhang: document.getElementById('compatLeftOverhang').value,
      right_overhang: document.getElementById('compatRightOverhang').value,
      min_overlap: Number(document.getElementById('compatMinOverlap').value),
    }));
  } catch (e) { show(String(e)); }
}

function filteredLigationProducts(result) {
  const allProducts = Array.isArray(result.products) ? result.products : [];
  const mode = document.getElementById('ligGraphFilter')?.value || 'all';
  if (mode === 'desired') {
    return allProducts
      .map((p, idx) => ({ ...p, _orig_idx: idx }))
      .filter((p) => p.class === 'desired_insert');
  }
  if (mode === 'byproducts') {
    return allProducts
      .map((p, idx) => ({ ...p, _orig_idx: idx }))
      .filter((p) => p.class !== 'desired_insert');
  }
  return allProducts.map((p, idx) => ({ ...p, _orig_idx: idx }));
}

function renderLigationGraph(result) {
  const host = document.getElementById('ligationGraph');
  const products = filteredLigationProducts(result);
  if (!products.length) {
    host.textContent = 'No ligation products match the current graph filter.';
    return;
  }
  const w = 980;
  const h = Math.max(260, 140 + products.length * 92);
  const srcX = 120;
  const dstX = 700;
  const vectorY = 70;
  const insertY = 150;
  const yForProduct = (idx) => 70 + idx * 92;
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));

  const sourceNodes = [
    { id: 'vector', x: srcX, y: vectorY, label: 'Vector', color: '#0369a1' },
    { id: 'insert', x: srcX, y: insertY, label: 'Insert', color: '#16a34a' },
  ];
  const prodNodes = products.map((p, idx) => ({
    id: `p${idx}`,
    x: dstX,
    y: yForProduct(idx),
    p,
    label: `${p.class} (${p.orientation})`,
  }));

  const edges = [];
  for (const n of prodNodes) {
    const prob = Number(n.p.predicted_probability || 0);
    edges.push({ from: 'vector', to: n.id, width: 1 + prob * 9, prob });
    edges.push({ from: 'insert', to: n.id, width: 1 + prob * 9, prob });
  }

  const nodeById = {};
  for (const n of sourceNodes) nodeById[n.id] = n;
  for (const n of prodNodes) nodeById[n.id] = n;

  const edgeSvg = edges.map((e) => {
    const a = nodeById[e.from];
    const b = nodeById[e.to];
    const midX = (a.x + b.x) / 2;
    const d = `M ${a.x+54} ${a.y} C ${midX} ${a.y}, ${midX} ${b.y}, ${b.x-94} ${b.y}`;
    return `<path d="${d}" class="lig-edge" stroke-width="${e.width.toFixed(2)}"></path>`;
  }).join('');

  const sourceSvg = sourceNodes.map((n) => (
    `<g class="lig-node" data-lig-node="${n.id}">` +
      `<rect x="${n.x-56}" y="${n.y-26}" width="112" height="40" rx="12" fill="${n.color}" opacity="0.93"></rect>` +
      `<text x="${n.x}" y="${n.y}" text-anchor="middle" font-size="13" font-family="Menlo, monospace" fill="white">${n.label}</text>` +
    `</g>`
  )).join('');

  const prodSvg = prodNodes.map((n, idx) => {
    const p = n.p;
    const prob = clamp(Number(p.predicted_probability || 0), 0, 1);
    const barW = Math.round(prob * 160);
    const fill = p.class === 'desired_insert' ? '#0f766e' : '#b45309';
    return (
      `<g class="lig-node" data-lig-product="${idx}">` +
        `<rect x="${n.x-90}" y="${n.y-32}" width="210" height="64" rx="12" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.6"></rect>` +
        `<text x="${n.x-76}" y="${n.y-10}" font-size="11" font-family="Menlo, monospace" fill="#0f172a">${p.class}</text>` +
        `<text x="${n.x-76}" y="${n.y+6}" font-size="10" font-family="Menlo, monospace" fill="#334155">${p.orientation}</text>` +
        `<text x="${n.x+112}" y="${n.y-10}" text-anchor="end" font-size="10" font-family="Menlo, monospace" fill="#334155">${p.length} bp</text>` +
        `<rect x="${n.x-76}" y="${n.y+12}" width="160" height="8" rx="4" fill="#e2e8f0"></rect>` +
        `<rect x="${n.x-76}" y="${n.y+12}" width="${barW}" height="8" rx="4" fill="${fill}"></rect>` +
        `<text x="${n.x+112}" y="${n.y+20}" text-anchor="end" font-size="10" font-family="Menlo, monospace" fill="${fill}">${(prob*100).toFixed(1)}%</text>` +
      `</g>`
    );
  }).join('');

  host.innerHTML = `
    <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}">
      <defs>
        <linearGradient id="ligBg" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#f8fafc"></stop>
          <stop offset="100%" stop-color="#fef9c3"></stop>
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="${w}" height="${h}" fill="url(#ligBg)"></rect>
      ${edgeSvg}
      ${sourceSvg}
      ${prodSvg}
      <text x="18" y="20" font-size="12" font-family="Menlo, monospace" fill="#334155">Ligation pathway graph (click nodes for details)</text>
    </svg>
  `;

  host.querySelectorAll('[data-lig-node]').forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.getAttribute('data-lig-node');
      if (id === 'vector') {
        setInspectorText(`Ligation source: Vector\nLength: ${plainSeq(document.getElementById('destVector').value).length} bp`);
      } else if (id === 'insert') {
        setInspectorText(`Ligation source: Insert\nLength: ${plainSeq(document.getElementById('entryClone').value).length} bp`);
      }
    });
  });
  host.querySelectorAll('[data-lig-product]').forEach((el) => {
    el.addEventListener('click', () => {
      const idx = Number(el.getAttribute('data-lig-product'));
      const p = products[idx];
      if (!p) return;
      const junction = Array.isArray(p.junction_integrity) ? p.junction_integrity.slice(0, 2).map((j) => `${j.label}: scar=${j.scar_8bp}`).join('\n') : 'n/a';
      setInspectorText(
        `Ligation product #${(Number(p._orig_idx) + 1)}\n` +
        `Class: ${p.class}\n` +
        `Orientation: ${p.orientation}\n` +
        `Length: ${p.length} bp\n` +
        `Predicted probability: ${(Number(p.predicted_probability || 0) * 100).toFixed(2)}%\n` +
        `Condition score: ${p.condition_adjusted_score || '-'}\n` +
        `Junctions:\n${junction}`
      );
    });
  });
}

function refreshLigationGraph() {
  if (!lastLigationResult) {
    setInspectorText('Run ligation simulation first to populate graph data.');
    return;
  }
  renderLigationGraph(lastLigationResult);
  show({ ligation_graph_filter: document.getElementById('ligGraphFilter').value });
}

function focusTopLigationProduct() {
  if (!lastLigationResult || !Array.isArray(lastLigationResult.products) || !lastLigationResult.products.length) {
    setInspectorText('No ligation products available. Run simulation first.');
    return;
  }
  const top = lastLigationResult.products[0];
  setInspectorText(
    `Top ligation product\n` +
    `Class: ${top.class}\n` +
    `Orientation: ${top.orientation}\n` +
    `Probability: ${(Number(top.predicted_probability || 0) * 100).toFixed(2)}%\n` +
    `Length: ${top.length} bp`
  );
}

async function runLigationSim() {
  try {
    const r = await callApi('/api/ligation-sim', {
      vector_sequence: document.getElementById('destVector').value,
      insert_sequence: document.getElementById('entryClone').value,
      vector_left_enzyme: document.getElementById('ligVecLeft').value,
      vector_right_enzyme: document.getElementById('ligVecRight').value,
      insert_left_enzyme: document.getElementById('ligInsLeft').value,
      insert_right_enzyme: document.getElementById('ligInsRight').value,
      derive_from_sequence: document.getElementById('ligDeriveSeq').checked,
      include_byproducts: document.getElementById('ligByproducts').checked,
      temp_c: Number(document.getElementById('ligTempC').value),
      ligase_units: Number(document.getElementById('ligaseUnits').value),
      vector_insert_ratio: Number(document.getElementById('ligVecInsRatio').value),
      dna_ng: Number(document.getElementById('ligDnaNg').value),
      phosphatase_treated_vector: document.getElementById('ligPhosphatase').checked,
      star_activity_level: Number(document.getElementById('ligStarActivity').value),
    });
    lastLigationResult = r;
    renderLigationGraph(r);
    show(r);
  } catch (e) { show(String(e)); }
}

async function runInFusion() {
  try {
    const fragments = JSON.parse(document.getElementById('inFusionFrags').value);
    show(await callApi('/api/in-fusion', {
      fragments,
      min_overlap: Number(document.getElementById('inFusionOverlap').value),
      circular: false,
    }));
  } catch (e) { show(String(e)); }
}

async function runOverlapPCR() {
  try {
    show(await callApi('/api/overlap-extension-pcr', {
      fragment_a: document.getElementById('oeA').value,
      fragment_b: document.getElementById('oeB').value,
      min_overlap: Number(document.getElementById('oeOverlap').value),
    }));
  } catch (e) { show(String(e)); }
}
