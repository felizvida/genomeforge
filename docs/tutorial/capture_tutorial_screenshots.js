#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..', '..');
const DATASET_FASTA = path.join(__dirname, 'datasets', 'training_real_world_sequences.fasta');
const OUTPUT_DIR = path.join(__dirname, 'assets', 'screenshots');
const BASE_URL = process.env.GENOMEFORGE_SCREENSHOT_BASE_URL || 'http://127.0.0.1:4173';

function parseFasta(text) {
  const records = {};
  let name = null;
  let chunks = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line) continue;
    if (line.startsWith('>')) {
      if (name) records[name] = chunks.join('');
      name = line.slice(1).trim();
      chunks = [];
    } else {
      chunks.push(line.trim());
    }
  }
  if (name) records[name] = chunks.join('');
  return records;
}

function derivedEgfpVariants(egfp) {
  const y67h = egfp.slice(0, 198) + 'CAC' + egfp.slice(201);
  const s204y = egfp.slice(0, 609) + 'TAC' + egfp.slice(612);
  return { y67h, s204y };
}

function fasta(name, seq) {
  return `>${name}\n${seq}`;
}

async function activateTab(page, tabId) {
  await page.locator(`#tabs .tab[data-tab="${tabId}"]`).click();
  await page.waitForSelector(`#${tabId}.active`);
}

async function waitForStats(page) {
  await page.waitForFunction(() => {
    const el = document.getElementById('sLen');
    return el && el.textContent && el.textContent !== '-';
  });
}

async function setRecord(page, { name, sequence, topology = 'linear' }) {
  await page.locator('#name').fill(name);
  await page.locator('#topology').selectOption(topology);
  await page.locator('#content').fill(fasta(name, sequence));
  await page.locator('button[data-action="runInfo"]').first().click();
  await waitForStats(page);
  await page.waitForTimeout(200);
}

async function captureViewport(page, filename, anchorSelector = null) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  if (anchorSelector) {
    await page.locator(anchorSelector).scrollIntoViewIfNeeded();
    await page.waitForTimeout(250);
  }
  await page.screenshot({
    path: path.join(OUTPUT_DIR, filename),
    fullPage: false,
    animations: 'disabled',
  });
}

async function click(page, selector, waitMs = 350) {
  await page.locator(selector).click();
  await page.waitForTimeout(waitMs);
}

async function captureMapWorkflow(page, seqs) {
  await page.goto(BASE_URL);
  await waitForStats(page);
  await setRecord(page, { name: 'pUC19_MCS', sequence: seqs.pUC19_MCS, topology: 'circular' });
  await page.locator('#enzymes').fill('EcoRI,BamHI,HindIII,XbaI,PstI,KpnI');
  await click(page, '#tab-map [data-action="runDigest"]');
  await click(page, '#tab-map [data-action="runMap"]');
  await page.waitForSelector('#map svg');
  await captureViewport(page, 'flagship_case_a_map.png', '#map');
}

async function captureSequenceTrackWorkflow(page, seqs) {
  await page.goto(BASE_URL);
  await waitForStats(page);
  await setRecord(page, { name: 'EGFP_CDS', sequence: seqs.EGFP_CDS, topology: 'linear' });
  await page.locator('#trackStart').fill('1');
  await page.locator('#trackEnd').fill('180');
  await page.locator('#trackFrame').selectOption('1');
  await page.getByRole('button', { name: 'Render Sequence Track' }).click();
  await page.waitForTimeout(350);
  await page.waitForSelector('#seqTrack svg');
  await captureViewport(page, 'flagship_case_d_track.png', '#seqTrack');
}

async function captureLigationWorkflow(page, seqs) {
  await page.goto(BASE_URL);
  await waitForStats(page);
  await activateTab(page, 'tab-advanced');
  await setRecord(page, { name: 'pUC19_MCS', sequence: seqs.pUC19_MCS, topology: 'circular' });
  await page.locator('#destVector').fill(seqs.pUC19_MCS);
  await page.locator('#entryClone').fill(seqs.EGFP_CDS.slice(0, 90));
  await click(page, '#tab-advanced [data-action="runLigationSim"]', 500);
  await page.waitForSelector('#ligationGraph svg');
  await click(page, 'button[data-action="focusTopLigationProduct"]');
  await captureViewport(page, 'flagship_case_g_ligation.png', '#ligationGraph');
}

async function captureMsaWorkflow(page, seqs) {
  await page.goto(BASE_URL);
  await waitForStats(page);
  const { y67h, s204y } = derivedEgfpVariants(seqs.EGFP_CDS);
  await activateTab(page, 'tab-advanced');
  await page.locator('#multiAlignSeqs').fill([
    seqs.EGFP_CDS.slice(0, 180),
    y67h.slice(0, 180),
    s204y.slice(0, 180),
    seqs.mCherry_CDS.slice(0, 180),
  ].join('\n'));
  await click(page, '#tab-advanced [data-action="runMSA"]', 600);
  await click(page, '#tab-advanced [data-action="runMSAHeatmap"]', 600);
  await page.waitForSelector('#msaHeatmap svg');
  await captureViewport(page, 'flagship_case_h_heatmap.png', '#msaHeatmap');
}

async function captureComparisonWorkflow(page, seqs) {
  await page.goto(BASE_URL);
  await waitForStats(page);
  const { y67h } = derivedEgfpVariants(seqs.EGFP_CDS);
  await activateTab(page, 'tab-advanced');
  await setRecord(page, { name: 'EGFP_CDS', sequence: seqs.EGFP_CDS, topology: 'linear' });
  await page.locator('#compareSeqA').fill('');
  await page.locator('#compareSeqB').fill(y67h);
  await page.locator('#compareWindow').fill('45');
  await click(page, '#tab-advanced [data-action="runComparisonLensViz"]', 500);
  await page.waitForSelector('#compareLensViz svg');
  await captureViewport(page, 'flagship_case_af_compare.png', '#compareLensViz');
}

async function captureTraceWorkflow(page, seqs) {
  await page.goto(BASE_URL);
  await waitForStats(page);
  await activateTab(page, 'tab-trace');
  await page.locator('#traceReference').fill(seqs.EGFP_CDS);
  await click(page, '#tab-trace [data-action="runImportAb1"]', 500);
  await click(page, '#tab-trace [data-action="runTraceChromatogram"]', 500);
  await page.waitForSelector('#traceChromViz svg');
  await captureViewport(page, 'flagship_case_ah_trace.png', '#traceChromViz');
}

async function captureBlastWorkflow(page, seqs) {
  await page.goto(BASE_URL);
  await waitForStats(page);
  await activateTab(page, 'tab-advanced');
  await page.locator('#blastQuery').fill(seqs.EGFP_CDS.slice(0, 42));
  await page.locator('#blastDb').fill([
    seqs.EGFP_CDS,
    seqs.mCherry_CDS,
    seqs.lacZ_alpha_fragment,
    seqs.BRAF_exon15_fragment,
  ].join('\n'));
  await page.locator('#blastKmer').fill('8');
  await page.locator('#blastTopHits').fill('4');
  await click(page, '#tab-advanced [data-action="runBlastSearch"]', 500);
  await page.waitForFunction(() => {
    const el = document.getElementById('out');
    return el && el.textContent && el.textContent.includes('"hits"');
  });
  await captureViewport(page, 'flagship_case_aj_blast.png', '#out');
}

async function captureHistoryWorkflow(page, seqs) {
  await page.goto(BASE_URL);
  await waitForStats(page);
  await activateTab(page, 'tab-advanced');
  const projectName = 'tutorial_release_project';
  await page.locator('#projectName').fill(projectName);
  await setRecord(page, { name: 'EGFP_CDS', sequence: seqs.EGFP_CDS, topology: 'linear' });
  await click(page, '#tab-advanced [data-action="runProjectSave"]', 500);
  const edited = seqs.EGFP_CDS.slice(0, 198) + 'CAC' + seqs.EGFP_CDS.slice(201);
  await setRecord(page, { name: 'EGFP_Y67H_training_variant', sequence: edited, topology: 'linear' });
  await page.locator('#projectName').fill(projectName);
  await click(page, '#tab-advanced [data-action="runProjectSave"]', 500);
  await click(page, '#tab-advanced [data-action="runProjectHistoryGraph"]', 500);
  await page.waitForSelector('#historyGraph svg');
  await captureViewport(page, 'flagship_case_ab_history.png', '#historyGraph');
}

async function main() {
  const seqs = parseFasta(fs.readFileSync(DATASET_FASTA, 'utf8'));
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1220 } });
  try {
    await captureMapWorkflow(page, seqs);
    await captureSequenceTrackWorkflow(page, seqs);
    await captureLigationWorkflow(page, seqs);
    await captureMsaWorkflow(page, seqs);
    await captureComparisonWorkflow(page, seqs);
    await captureTraceWorkflow(page, seqs);
    await captureBlastWorkflow(page, seqs);
    await captureHistoryWorkflow(page, seqs);
  } finally {
    await browser.close();
  }
  console.log(`Wrote screenshots to ${OUTPUT_DIR}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
