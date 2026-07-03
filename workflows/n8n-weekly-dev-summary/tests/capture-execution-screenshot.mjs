#!/usr/bin/env node
/**
 * Opens imported workflow in n8n, executes it, captures execution screenshot.
 */
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const out = join(__dirname, '..', 'assets', 'n8n-execution-screenshot.png');

async function dismissOverlays(page) {
  for (const label of [/skip/i, /close/i, /dismiss/i, /got it/i, /later/i]) {
    const btn = page.getByRole('button', { name: label });
    if (await btn.count()) {
      await btn.first().click({ force: true }).catch(() => {});
      await page.waitForTimeout(500);
    }
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
}

const browser = await chromium.launch({
  headless: true,
  executablePath: '/usr/bin/chromium',
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

try {
  await page.goto('http://localhost:5678', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(2000);

  const setupHeading = page.getByText('Set up owner account');
  if (await setupHeading.count()) {
    const inputs = page.locator('input');
    const count = await inputs.count();
    for (let i = 0; i < count; i++) {
      const type = await inputs.nth(i).getAttribute('type');
      if (type === 'email') await inputs.nth(i).fill('owner@test.local');
      else if (type === 'password') await inputs.nth(i).fill('BountyTest1');
      else if (type === 'text') {
        const label = await inputs.nth(i).getAttribute('placeholder');
        if (label?.toLowerCase().includes('first') || i === 1) await inputs.nth(i).fill('Bounty');
        else await inputs.nth(i).fill('Test');
      }
    }
    await page.getByRole('button', { name: /next/i }).click();
    await page.waitForTimeout(4000);
  }

  const signinEmail = page.locator('input[type="email"]');
  if (await signinEmail.count()) {
    await signinEmail.first().fill('owner@test.local');
    await page.locator('input[type="password"]').first().fill('BountyTest1');
    const loginBtn = page.getByRole('button', { name: /sign in|log in/i });
    if (await loginBtn.count()) await loginBtn.first().click();
    await page.waitForTimeout(3000);
  }

  await page.goto('http://localhost:5678/workflow/weekly-github-dev-summary', {
    waitUntil: 'domcontentloaded',
  });
  await page.waitForTimeout(2000);
  await dismissOverlays(page);

  const editorTab = page.getByRole('tab', { name: /editor/i });
  if (await editorTab.count()) await editorTab.first().click();

  const executeBtn = page.getByRole('button', { name: /execute workflow|test workflow/i });
  if (await executeBtn.count()) {
    await executeBtn.first().click();
    await page.waitForTimeout(18000);
  }

  await dismissOverlays(page);
  await page.screenshot({ path: out, fullPage: false });
  console.log(`Screenshot saved: ${out}`);
} catch (err) {
  console.error('Screenshot failed:', err.message);
  process.exit(1);
} finally {
  await browser.close();
}
