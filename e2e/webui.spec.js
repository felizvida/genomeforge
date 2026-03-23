const { test, expect } = require('@playwright/test');

async function waitForInitialStats(page) {
  await expect(page.locator('#sLen')).not.toHaveText('-');
}

async function activateTab(page, tabId) {
  await page.locator(`#tabs .tab[data-tab="${tabId}"]`).click();
  await expect(page.locator(`#${tabId}`)).toHaveClass(/active/);
}

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await waitForInitialStats(page);
});

test('renders edited map and sequence track', async ({ page }) => {
  await activateTab(page, 'tab-edit');
  await page.locator('#editValue').fill('TTAA');
  await page.locator('button[data-action="applyEditToBuffer"]').first().click();
  await expect(page.locator('#content')).toHaveValue(/TTAA/);

  await page.locator('button[data-action="runMap"]').first().click();
  await expect(page.locator('#map svg')).toBeVisible();

  await page.locator('button[data-action="runSequenceTrack"]').first().click();
  await expect(page.locator('#seqTrack svg')).toBeVisible();
});

test('runs trace import, chromatogram, and BLAST-like search', async ({ page }) => {
  await activateTab(page, 'tab-trace');
  await page.locator('#tab-trace [data-action="runImportAb1"]').click();
  await expect(page.locator('#traceId')).not.toHaveValue('');

  await page.locator('#tab-trace [data-action="runTraceChromatogram"]').click();
  await expect(page.locator('#traceChromViz svg')).toBeVisible();

  await activateTab(page, 'tab-advanced');
  await page.locator('#tab-advanced [data-action="runBlastSearch"]').click();
  await expect(page.locator('#out')).toContainText('"hits"');
});

test('runs analysis and cloning workflows', async ({ page }) => {
  await activateTab(page, 'tab-advanced');

  await page.locator('#tab-advanced [data-action="runPairwiseAlign"]').click();
  await expect(page.locator('#out')).toContainText('"identity_pct"');

  await page.locator('#tab-advanced [data-action="runGibsonAssemble"]').click();
  await expect(page.locator('#out')).toContainText('"assembled_length"');

  await page.locator('#tab-advanced [data-action="runLigationSim"]').click();
  await expect(page.locator('#ligationGraph svg')).toBeVisible();
  await page.locator('[data-action="focusTopLigationProduct"]').click();
  await expect(page.locator('#inspector')).toContainText('Top ligation product');
});

test('saves and reloads a project from the browser UI', async ({ page }) => {
  const projectName = `e2e_project_${Date.now()}`;
  const savedContent = '>e2e_project\nGAATTCCGGATCCATGGCCATTGTAATGGGCC';

  await activateTab(page, 'tab-advanced');
  await page.locator('#projectName').fill(projectName);
  await page.locator('#name').fill('e2e_project');
  await page.locator('#content').fill(savedContent);

  await page.locator('#tab-advanced [data-action="runProjectSave"]').click();
  await expect(page.locator('#out')).toContainText('"saved": true');

  await page.locator('#content').fill('>temporary\nTTTTTTTTTTTT');
  await page.locator('#tab-advanced [data-action="runProjectLoad"]').click();
  await expect(page.locator('#content')).toHaveValue(savedContent);
});

test('adds a feature and inspects it from the map', async ({ page }) => {
  const featureLabel = `e2e_feature_${Date.now()}`;

  await activateTab(page, 'tab-advanced');
  await page.locator('#featKey').fill('promoter');
  await page.locator('#featLoc').fill('3..18');
  await page.locator('#featLabel').fill(featureLabel);
  await page.locator('#tab-advanced [data-action="runFeatureAdd"]').click();
  await expect(page.locator('#out')).toContainText(featureLabel);

  await page.locator('button[data-action="runMap"]').first().click();
  await expect(page.locator('#map svg')).toBeVisible();
  await page.locator('#map .feature-label').filter({ hasText: featureLabel }).first().click({ force: true });
  await expect(page.locator('#inspector')).toContainText(featureLabel);
});

test('creates a share bundle and opens the share page', async ({ page }) => {
  const projectName = `e2e_share_project_${Date.now()}`;
  const collectionName = `e2e_collection_${Date.now()}`;

  await activateTab(page, 'tab-edit');
  await page.locator('#editValue').fill('GGCC');
  await page.locator('button[data-action="applyEditToBuffer"]').first().click();

  await activateTab(page, 'tab-advanced');
  await page.locator('#projectName').fill(projectName);
  await page.locator('#collectionName').fill(collectionName);
  await page.locator('#collectionProjects').fill(projectName);
  await page.locator('#name').fill(projectName);

  await page.locator('#tab-advanced [data-action="runProjectSave"]').click();
  await expect(page.locator('#out')).toContainText('"saved": true');

  await page.locator('#tab-advanced [data-action="runProjectHistoryGraph"]').click();
  await expect(page.locator('#historyGraph svg')).toBeVisible();

  await page.locator('#tab-advanced [data-action="runShareCreate"]').click();
  await expect(page.locator('#shareId')).not.toHaveValue('');
  const shareId = await page.locator('#shareId').inputValue();

  await page.goto(`/share/${shareId}`);
  await expect(page.locator('h1')).toContainText(`Shared Bundle ${shareId}`);
  await expect(page.locator('body')).toContainText(projectName);
});
