const { expect } = require('@playwright/test');

async function waitForInitialStats(page) {
  await expect(page.locator('#sLen')).not.toHaveText('-');
}

async function activateTab(page, tabId) {
  await page.locator(`#tabs .tab[data-tab="${tabId}"]`).click();
  await expect(page.locator(`#${tabId}`)).toHaveClass(/active/);
}

async function clickAction(page, selector, expectedText = null) {
  const before = await page.locator('#out').innerText().catch(() => '');
  await page.locator(selector).click();
  if (expectedText) {
    await page.waitForFunction(
      ({ beforeText, needle }) => {
        const out = document.querySelector('#out');
        return out && out.innerText !== beforeText && out.innerText.includes(needle);
      },
      { beforeText: before, needle: expectedText },
      { timeout: 10000 },
    );
    await expect(page.locator('#out')).toContainText(expectedText);
  }
}

async function readOutJson(page) {
  return JSON.parse(await page.locator('#out').innerText());
}

async function expectOutError(page, message) {
  await expect(page.locator('#out')).toContainText(`Error: ${message}`);
}

async function saveProjectFromUi(page, projectName, content, recordName = projectName) {
  await activateTab(page, 'tab-advanced');
  await page.locator('#projectName').fill(projectName);
  await page.locator('#name').fill(recordName);
  await page.locator('#content').fill(content);
  await clickAction(page, '#tab-advanced [data-action="runProjectSave"]', '"saved": true');
}

module.exports = {
  activateTab,
  clickAction,
  expectOutError,
  readOutJson,
  saveProjectFromUi,
  waitForInitialStats,
};
