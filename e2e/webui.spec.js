const { test, expect } = require('@playwright/test');

async function waitForInitialStats(page) {
  await expect(page.locator('#sLen')).not.toHaveText('-');
}

async function activateTab(page, tabId) {
  await page.locator(`#tabs .tab[data-tab="${tabId}"]`).click();
  await expect(page.locator(`#${tabId}`)).toHaveClass(/active/);
}

async function clickAction(page, selector, expectedText = null) {
  await page.locator(selector).click();
  if (expectedText) {
    await expect(page.locator('#out')).toContainText(expectedText);
  }
}

async function saveProjectFromUi(page, projectName, content, recordName = projectName) {
  await activateTab(page, 'tab-advanced');
  await page.locator('#projectName').fill(projectName);
  await page.locator('#name').fill(recordName);
  await page.locator('#content').fill(content);
  await clickAction(page, '#tab-advanced [data-action="runProjectSave"]', '"saved": true');
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

  await saveProjectFromUi(page, projectName, savedContent, 'e2e_project');

  await page.locator('#content').fill('>temporary\nTTTTTTTTTTTT');
  await clickAction(page, '#tab-advanced [data-action="runProjectLoad"]');
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

  await clickAction(page, '#tab-advanced [data-action="runProjectSave"]', '"saved": true');

  await clickAction(page, '#tab-advanced [data-action="runProjectHistoryGraph"]');
  await expect(page.locator('#historyGraph svg')).toBeVisible();

  await clickAction(page, '#tab-advanced [data-action="runShareCreate"]');
  await expect(page.locator('#shareId')).not.toHaveValue('');
  const shareId = await page.locator('#shareId').inputValue();

  await page.goto(`/share/${shareId}`);
  await expect(page.locator('h1')).toContainText(`Shared Bundle ${shareId}`);
  await expect(page.locator('body')).toContainText(projectName);
});

test('manages collection workflows from the browser UI', async ({ page }) => {
  const projectName = `e2e_collection_project_${Date.now()}`;
  const collectionName = `e2e_collection_${Date.now()}`;

  await saveProjectFromUi(page, projectName, `>${projectName}\nGAATTCCGGATCCATGGCCATTGTAATGGGCC`);

  await page.locator('#collectionName').fill(collectionName);
  await page.locator('#collectionProjects').fill(projectName);
  await clickAction(page, '#tab-advanced [data-action="runCollectionSave"]', '"saved": true');

  await page.locator('#collectionProjects').fill('');
  await clickAction(page, '#tab-advanced [data-action="runCollectionLoad"]');
  await expect(page.locator('#collectionProjects')).toHaveValue(projectName);

  await clickAction(page, '#tab-advanced [data-action="runCollectionAddProject"]', '"saved": true');
});

test('runs review and permission workflows from the browser UI', async ({ page }) => {
  const projectName = `e2e_review_project_${Date.now()}`;
  const workspaceName = `e2e_workspace_${Date.now()}`;

  await saveProjectFromUi(page, projectName, `>${projectName}\nGAATTCCGGATCCATGGCCATTGTAATGGGCC`);

  await page.locator('#workspaceName').fill(workspaceName);
  await page.locator('#workspaceOwner').fill('owner_user');
  await page.locator('#workspaceMembers').fill('reviewer_user,editor_user');
  await clickAction(page, '#tab-advanced [data-action="runWorkspaceCreate"]', '"created": true');

  await page.locator('#permProjectName').fill(projectName);
  await page.locator('#reviewProjectName').fill(projectName);
  await page.locator('#permRole').selectOption('reviewer');
  await clickAction(page, '#tab-advanced [data-action="runProjectPermissionsSet"]', '"saved": true');

  await clickAction(page, '#tab-advanced [data-action="runReviewSubmit"]', '"submitted": true');
  await expect(page.locator('#reviewId')).not.toHaveValue('');

  await clickAction(page, '#tab-advanced [data-action="runReviewApprove"]', '"approved": true');
  await expect(page.locator('#out')).toContainText('"status": "approved"');
});

test('shows project audit log and diff from the browser UI', async ({ page }) => {
  const baseName = `e2e_audit_base_${Date.now()}`;
  const variantName = `e2e_audit_variant_${Date.now()}`;
  const baseContent = `>${baseName}\nGAATTCCGGATCCATGGCCATTGTAATGGGCC`;
  const variantContent = `>${variantName}\nGAATTCCGGATCCATGGCCATTGTAAAGGGCC`;

  await saveProjectFromUi(page, baseName, baseContent);
  await saveProjectFromUi(page, variantName, variantContent);

  await page.locator('#permProjectName').fill(baseName);
  await page.locator('#reviewProjectName').fill(baseName);
  await page.locator('#reviewSubmitter').fill('editor_user');
  await page.locator('#reviewerName').fill('reviewer_user');
  await page.locator('#permRole').selectOption('reviewer');
  await clickAction(page, '#tab-advanced [data-action="runProjectPermissionsSet"]', '"saved": true');
  await clickAction(page, '#tab-advanced [data-action="runReviewSubmit"]', '"submitted": true');
  await expect(page.locator('#reviewId')).not.toHaveValue('');
  await clickAction(page, '#tab-advanced [data-action="runReviewApprove"]', '"approved": true');

  await clickAction(page, '#tab-advanced [data-action="runProjectAuditLogGet"]', '"events"');
  await expect(page.locator('#out')).toContainText('"action": "project_save"');
  await expect(page.locator('#out')).toContainText('"action": "review_approve"');

  await page.locator('#projectName').fill(baseName);
  await page.locator('#permProjectName').fill(variantName);
  await clickAction(page, '#tab-advanced [data-action="runProjectDiff"]', '"sequence_identity_pct"');
  await expect(page.locator('#out')).toContainText('"sequence_change_count"');
  await expect(page.locator('#out')).toContainText('"name_a"');
  await expect(page.locator('#out')).toContainText('"name_b"');
});
