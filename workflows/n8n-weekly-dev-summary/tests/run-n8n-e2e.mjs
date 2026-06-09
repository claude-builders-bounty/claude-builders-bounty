#!/usr/bin/env node
/**
 * End-to-end n8n test with mocked Anthropic + Discord endpoints.
 * Produces assets/n8n-execution-screenshot.png with a successful run.
 */
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { spawn, execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { chromium } from 'playwright';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const screenshotPath = join(root, 'assets', 'n8n-execution-screenshot.png');
const n8nHome = join(root, '.n8n-e2e');
const workflowPath = join(root, 'weekly-dev-summary.e2e.json');
const mockPort = 19999;

mkdirSync(join(root, 'assets'), { recursive: true });
mkdirSync(n8nHome, { recursive: true });

const mockSummary =
  'Highlights: steady maintenance week. Commits: documentation and CI updates. Issues Resolved: none. Pull Requests Merged: none. TL;DR: quiet week with infra polish.';

const server = createServer((req, res) => {
  let body = '';
  req.on('data', (chunk) => {
    body += chunk;
  });
  req.on('end', () => {
    if (req.url?.startsWith('/v1/messages') && req.method === 'POST') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          content: [{ type: 'text', text: mockSummary }],
          model: 'claude-sonnet-4-20250514',
          role: 'assistant',
        }),
      );
      return;
    }
    if (req.url?.startsWith('/discord') && req.method === 'POST') {
      res.writeHead(204);
      res.end();
      return;
    }
    res.writeHead(404);
    res.end('not found');
  });
});

await new Promise((resolve) => server.listen(mockPort, '127.0.0.1', resolve));

const workflow = JSON.parse(readFileSync(join(root, 'weekly-dev-summary.json'), 'utf8'));
const e2eWorkflow = JSON.parse(
  JSON.stringify(workflow).replaceAll(
    'https://api.anthropic.com/v1/messages',
    `http://127.0.0.1:${mockPort}/v1/messages`,
  ),
);

// n8n CLI/UI execution requires a manual trigger, not a schedule trigger.
const trigger = e2eWorkflow.nodes.find((n) => n.name === 'Friday 5pm Weekly Trigger');
if (trigger) {
  trigger.type = 'n8n-nodes-base.manualTrigger';
  trigger.typeVersion = 1;
  trigger.name = 'Manual Test Trigger';
  delete trigger.parameters;
}

const connections = e2eWorkflow.connections;
if (connections['Friday 5pm Weekly Trigger']) {
  connections['Manual Test Trigger'] = connections['Friday 5pm Weekly Trigger'];
  delete connections['Friday 5pm Weekly Trigger'];
}

writeFileSync(workflowPath, JSON.stringify([e2eWorkflow]));

const env = {
  ...process.env,
  N8N_USER_FOLDER: n8nHome,
  N8N_PORT: '5678',
  N8N_HOST: '127.0.0.1',
  N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS: 'false',
  N8N_DIAGNOSTICS_ENABLED: 'false',
  N8N_PERSONALIZATION_ENABLED: 'false',
  N8N_SECURE_COOKIE: 'false',
  N8N_RUNNERS_ENABLED: 'true',
  GITHUB_REPO: process.env.GITHUB_REPO || 'claude-builders-bounty/claude-builders-bounty',
  GITHUB_TOKEN: process.env.GITHUB_TOKEN || '',
  ANTHROPIC_API_KEY: 'e2e-test-key',
  DELIVERY_CHANNEL: 'discord',
  DISCORD_WEBHOOK_URL: `http://127.0.0.1:${mockPort}/discord`,
  SUMMARY_LANGUAGE: 'EN',
};

if (!env.GITHUB_TOKEN) {
  console.error('GITHUB_TOKEN required for e2e test');
  process.exit(1);
}

const n8nProc = spawn('n8n', ['start'], { env, stdio: ['ignore', 'pipe', 'pipe'] });
let n8nLog = '';
n8nProc.stdout.on('data', (d) => {
  n8nLog += d;
});
n8nProc.stderr.on('data', (d) => {
  n8nLog += d;
});

async function waitForN8n(timeoutMs = 90000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch('http://127.0.0.1:5678/healthz');
      if (res.ok) return;
    } catch (_) {
      if (n8nLog.includes('n8n ready')) return;
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error('n8n failed to start');
}

let exitCode = 0;
try {
  await waitForN8n();

  execSync(`n8n import:workflow --input="${workflowPath}"`, {
    env,
    stdio: 'pipe',
  });

  const raw = execSync('n8n execute --id=weekly-github-dev-summary --rawOutput', {
    env,
    stdio: 'pipe',
    timeout: 300000,
  }).toString();

  const result = JSON.parse(raw);
  const items = Array.isArray(result) ? result : [result];
  const summaryItem = items.find((item) => item.json?.summary) ?? items.at(-1);
  const summary = summaryItem?.json?.summary || summaryItem?.summary;
  if (!summary || !String(summary).includes('TL;DR')) {
    throw new Error('execute output missing generated summary');
  }

  const browser = await chromium.launch({
    headless: true,
    executablePath: '/usr/bin/chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:5678/workflow/weekly-github-dev-summary/executions/last', {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  });
  await page.waitForTimeout(4000);

  const successBadge = page.getByText(/succeeded|success/i);
  if (!(await successBadge.count())) {
    await page.goto('http://127.0.0.1:5678/workflow/weekly-github-dev-summary', {
      waitUntil: 'domcontentloaded',
      timeout: 60000,
    });
    await page.waitForTimeout(2000);
    const executeBtn = page.getByRole('button', { name: /execute workflow|test workflow/i });
    if (await executeBtn.count()) {
      await executeBtn.first().click();
      await page.waitForTimeout(20000);
    }
  }

  await page.screenshot({ path: screenshotPath, fullPage: false });
  await browser.close();

  console.log(`OK: n8n e2e execution succeeded; screenshot -> ${screenshotPath}`);
} catch (err) {
  console.error('E2E failed:', err.message);
  if (n8nLog) console.error(n8nLog.slice(-2000));
  exitCode = 1;
} finally {
  n8nProc.kill('SIGTERM');
  server.close();
}

process.exit(exitCode);
