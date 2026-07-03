#!/usr/bin/env node
/**
 * Regression tests for weekly-dev-summary n8n workflow JSON.
 * Run: node tests/validate-workflow.mjs
 */
import { readFileSync, statSync } from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const workflowPath = join(__dirname, '..', 'weekly-dev-summary.json');
const readmePath = join(__dirname, '..', 'README.md');
const ciWorkflowPath = join(__dirname, '..', '..', '..', '.github', 'workflows', 'test-n8n-weekly-summary.yml');
const workflow = JSON.parse(readFileSync(workflowPath, 'utf8'));
const readme = readFileSync(readmePath, 'utf8');
const ciWorkflow = readFileSync(ciWorkflowPath, 'utf8');

const failures = [];

function assert(condition, message) {
  if (!condition) failures.push(message);
}

const nodeTypes = workflow.nodes.map((n) => n.type);
const nodeNames = workflow.nodes.map((n) => n.name);

assert(workflow.name, 'workflow has a name');
assert(
  workflow.description?.includes('Claude Sonnet 4') && workflow.description.includes('EN/FR'),
  'workflow has importable description metadata for n8n UI',
);
assert(
  workflow.description?.includes('paginated') && workflow.description.includes('fail-fast'),
  'workflow description documents paginated GitHub fetches and fail-fast validation',
);
assert(
  workflow.description?.includes('7-day') && workflow.description.includes('parallel'),
  'workflow description documents rolling 7-day window and parallel GitHub fetches',
);
assert(Array.isArray(workflow.nodes) && workflow.nodes.length >= 8, 'workflow has enough nodes');
assert(workflow.connections && typeof workflow.connections === 'object', 'workflow has connections map');
assert(workflow.settings?.executionOrder, 'workflow has execution settings for n8n import');
assert(workflow.settings?.timezone, 'workflow defines a timezone for the Friday 5pm cron');
assert(
  workflow.nodes.every((n) => n.id && n.name && n.type && Array.isArray(n.position)),
  'every node has id, name, type, and position for n8n canvas import',
);
assert(nodeTypes.includes('n8n-nodes-base.scheduleTrigger'), 'has schedule trigger');
assert(nodeTypes.filter((t) => t === 'n8n-nodes-base.httpRequest').length >= 3, 'has Claude + delivery HTTP nodes');
assert(nodeNames.includes('Claude API'), 'has Claude API node');

const trigger = workflow.nodes.find((n) => n.type === 'n8n-nodes-base.scheduleTrigger');
const interval = trigger?.parameters?.rule?.interval?.[0];
assert(interval?.field === 'weeks', 'trigger runs weekly');
assert(interval?.triggerAtDay?.includes(5), 'trigger runs on Friday');
assert(interval?.triggerAtHour === 17, 'trigger runs at 5pm');

const serialized = JSON.stringify(workflow);
assert(serialized.includes('claude-sonnet-4-20250514'), 'uses required Claude model');
assert(serialized.includes('GITHUB_REPO'), 'configurable GitHub repo');
assert(serialized.includes('DELIVERY_CHANNEL'), 'configurable delivery channel');
assert(serialized.includes('SUMMARY_LANGUAGE'), 'configurable language EN/FR');
assert(
  serialized.includes('DISCORD_WEBHOOK_URL') &&
    serialized.includes('SLACK_WEBHOOK_URL') &&
    serialized.includes('SUMMARY_EMAIL_TO'),
  'discord, slack, and email delivery configured',
);
assert(serialized.includes('api.github.com'), 'fetches GitHub API');
assert(serialized.includes('/commits'), 'fetches commits');
assert(serialized.includes('/issues'), 'fetches issues');
assert(serialized.includes('search/issues'), 'fetches merged PRs via GitHub search API');
assert(serialized.includes('api.anthropic.com/v1/messages'), 'calls Claude API');
assert(serialized.includes('$env.GITHUB_TOKEN'), 'GitHub token read from env at runtime');

const fetchNodes = workflow.nodes.filter((n) =>
  ['Fetch Commits', 'Fetch Closed Issues', 'Fetch Merged PRs'].includes(n.name),
);
assert(fetchNodes.length === 3, 'has three GitHub fetch nodes');
assert(
  fetchNodes.every((n) => n.type === 'n8n-nodes-base.code'),
  'GitHub fetch nodes use Code with pagination (not raw HTTP swallowing errors)',
);
assert(
  fetchNodes.every((n) => n.parameters?.jsCode?.includes('fetchGitHubPages')),
  'GitHub fetch nodes paginate API responses',
);

const loadConfig = workflow.nodes.find((n) => n.name === 'Load Config');
const loadCode = loadConfig?.parameters?.jsCode || '';
assert(
  loadCode.includes('GitHub-safe characters only'),
  'Load Config validates GITHUB_REPO format (prevents malformed owner/repo injection)',
);
assert(
  loadCode.includes('validateGitHubToken') && loadCode.includes('api.github.com/repos/'),
  'Load Config validates GITHUB_TOKEN via GET /repos/{owner}/{repo} before GitHub fetches',
);
assert(!loadCode.includes('api.github.com/user'), 'Load Config does not validate token via /user endpoint');
assert(loadCode.includes('weekStart.toISOString()'), 'Load Config emits ISO8601 weekStart');
assert(loadCode.includes('weekEnd: now.toISOString()'), 'Load Config emits ISO8601 weekEnd');
assert(!loadCode.includes('githubToken:'), 'Load Config does not embed githubToken in item JSON');
assert(!loadCode.includes('anthropicApiKey:'), 'Load Config does not embed anthropicApiKey in item JSON');
assert(loadCode.includes('emailTo:'), 'Load Config emits emailTo for email delivery');
assert(
  loadCode.includes('SUMMARY_EMAIL_TO must be a valid email address'),
  'Load Config validates SUMMARY_EMAIL_TO format for email delivery',
);
assert(
  loadCode.includes('SUMMARY_EMAIL_FROM must be a valid email address'),
  'Load Config validates SUMMARY_EMAIL_FROM format for email delivery',
);
const sendEmail = workflow.nodes.find((n) => n.name === 'Send Email');
const sendEmailTo = sendEmail?.parameters?.toEmail || '';
assert(
  sendEmailTo.includes('$json.config.emailTo') && loadCode.includes('emailTo:'),
  'Send Email.toEmail resolves to emailTo populated by Load Config',
);

const buildPrompt = workflow.nodes.find((n) => n.name === 'Build Claude Prompt');
const buildCode = buildPrompt?.parameters?.jsCode || '';
assert(buildPrompt?.parameters?.jsCode?.includes('merged_at'), 'filters merged PRs by date');
assert(
  buildCode.includes('!i.pull_request'),
  'closed issues filter excludes pull requests (GitHub /issues returns both)',
);
assert(buildPrompt?.parameters?.mode === 'runOnceForAllItems', 'Build Claude Prompt runs once after merge');
assert(buildCode.includes('collectRecords'), 'collects all GitHub HTTP items');
assert(buildCode.includes('isGitHubError'), 'collectRecords rejects GitHub error payloads');
assert(buildCode.includes('system:'), 'Claude request includes system prompt');
assert(buildCode.includes('JSON.stringify(activity'), 'sends structured activity JSON to Claude');
assert(
  buildCode.includes("language === 'FR'"),
  'Build Claude Prompt switches user instructions for FR language',
);
assert(
  buildCode.includes('systemPrompt') &&
    buildCode.includes('résumez l'),
  'Build Claude Prompt switches system instructions for FR language',
);

const claude = workflow.nodes.find((n) => n.name === 'Claude API');
assert(
  claude?.parameters?.headerParameters?.parameters?.some(
    (h) => h.name === 'x-api-key' && h.value?.includes('$env.ANTHROPIC_API_KEY'),
  ),
  'Claude API reads ANTHROPIC_API_KEY from env (not item JSON)',
);
assert(claude?.onError === 'continueRegularOutput', 'Claude API has graceful failure routing');

const mergeNode = workflow.nodes.find((n) => n.name === 'Merge GitHub Results');
assert(mergeNode?.parameters?.mode === 'append', 'Merge GitHub Results uses append mode (sync barrier for parallel fetches)');

const connections = workflow.connections || {};
assert(Object.keys(connections).includes('Friday 5pm Weekly Trigger'), 'trigger is wired');
assert(Object.keys(connections).includes('Claude API'), 'Claude node is wired');

function targets(source, index = 0) {
  return (connections[source]?.main?.[index] || []).map((edge) => edge.node);
}

const pipeline = [
  ['Friday 5pm Weekly Trigger', 'Load Config'],
  ['Load Config', 'Fetch Commits'],
  ['Load Config', 'Fetch Closed Issues'],
  ['Load Config', 'Fetch Merged PRs'],
  ['Fetch Commits', 'Merge GitHub Results'],
  ['Fetch Closed Issues', 'Merge GitHub Results'],
  ['Fetch Merged PRs', 'Merge GitHub Results'],
  ['Merge GitHub Results', 'Build Claude Prompt'],
  ['Build Claude Prompt', 'Claude API'],
  ['Claude API', 'Format Summary'],
  ['Format Summary', 'Route Delivery'],
];
for (const [source, target] of pipeline) {
  assert(targets(source).includes(target), `${source} connects to ${target}`);
}
assert(
  targets('Route Delivery', 0).includes('Send Discord') &&
    targets('Route Delivery', 1).includes('Send Slack') &&
    targets('Route Delivery', 2).includes('Send Email'),
  'Route Delivery connects to Discord, Slack, and Email nodes',
);

for (const node of workflow.nodes || []) {
  const code = node.parameters?.jsCode;
  if (code) {
    try {
      new vm.Script(`(async () => {\n${code}\n})`);
    } catch (error) {
      failures.push(`${node.name} contains invalid JavaScript: ${error.message}`);
    }
  }
}

assert(!ciWorkflow.includes('pull_request_target'), 'CI workflow does not use pull_request_target with fork checkout');
assert(!/pull_request_target:[\s\S]*checkout/.test(ciWorkflow), 'privileged CI trigger never checks out fork code');

const setupSteps = [...readme.matchAll(/^### \d+\./gm)];
assert(setupSteps.length > 0 && setupSteps.length <= 5, 'README setup uses five steps or fewer');
assert(readme.includes('weekly-dev-summary.json'), 'README points to importable workflow JSON');
assert(readme.includes('n8n-execution-screenshot.png'), 'README references n8n execution screenshot');

const screenshotPath = join(__dirname, '..', 'assets', 'n8n-execution-screenshot.png');
const screenshot = statSync(screenshotPath);
assert(screenshot.isFile() && screenshot.size > 1024, 'n8n execution screenshot asset exists and is non-trivial');

for (const forbidden of ['sk-ant-', 'ghp_', 'gho_', 'discord.com/api/webhooks/']) {
  assert(!serialized.includes(forbidden), `workflow does not embed ${forbidden} secrets`);
}

const requiredTestScripts = [
  'validate-workflow.mjs',
  'collect-github-data.test.mjs',
  'github-collect-unit.test.mjs',
  'workflow-integration.test.mjs',
  'delivery-verification.test.mjs',
  'peer-review-acceptance.test.mjs',
  'run-ci-checks.mjs',
  'github-fetch.test.mjs',
  'capture-execution-screenshot.mjs',
  'run-n8n-e2e.mjs',
];
const secretScanExempt = new Set(['validate-workflow.mjs']);
for (const file of requiredTestScripts) {
  const scriptPath = join(__dirname, file);
  const scriptText = readFileSync(scriptPath, 'utf8');
  assert(scriptText.startsWith('#!/usr/bin/env node'), `${file} has node shebang`);
  if (!secretScanExempt.has(file)) {
    for (const secret of ['sk-ant-', 'ghp_', 'gho_', 'discord.com/api/webhooks/']) {
      assert(!scriptText.includes(secret), `${file} does not embed ${secret}`);
    }
  }
}
const workflowPkg = JSON.parse(readFileSync(join(__dirname, '..', 'package.json'), 'utf8'));
assert(
  workflowPkg.scripts?.test?.includes('run-ci-checks.mjs'),
  'package.json npm test delegates to run-ci-checks.mjs',
);
assert(
  workflowPkg.scripts?.['test:github']?.includes('github-fetch.test.mjs'),
  'package.json test:github runs github-fetch.test.mjs',
);
assert(
  workflowPkg.scripts?.['test:peer-review']?.includes('peer-review-acceptance.test.mjs'),
  'package.json test:peer-review runs peer-review acceptance suite',
);
assert(
  workflowPkg.scripts?.['test:delivery']?.includes('delivery-verification.test.mjs'),
  'package.json test:delivery runs delivery verification suite',
);

if (failures.length) {
  console.error('FAILED:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log(`OK: ${workflow.nodes.length} nodes, all acceptance checks passed.`);
