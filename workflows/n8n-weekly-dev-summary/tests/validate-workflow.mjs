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
const workflow = JSON.parse(readFileSync(workflowPath, 'utf8'));
const readme = readFileSync(readmePath, 'utf8');

const failures = [];

function assert(condition, message) {
  if (!condition) failures.push(message);
}

const nodeTypes = workflow.nodes.map((n) => n.type);
const nodeNames = workflow.nodes.map((n) => n.name);

assert(workflow.name, 'workflow has a name');
assert(Array.isArray(workflow.nodes) && workflow.nodes.length >= 8, 'workflow has enough nodes');
assert(workflow.connections && typeof workflow.connections === 'object', 'workflow has connections map');
assert(workflow.settings?.executionOrder, 'workflow has execution settings for n8n import');
assert(workflow.settings?.timezone, 'workflow defines a timezone for the Friday 5pm cron');
assert(
  workflow.nodes.every((n) => n.id && n.name && n.type && Array.isArray(n.position)),
  'every node has id, name, type, and position for n8n canvas import',
);
assert(nodeTypes.includes('n8n-nodes-base.scheduleTrigger'), 'has schedule trigger');
assert(nodeTypes.filter((t) => t === 'n8n-nodes-base.httpRequest').length >= 4, 'has GitHub + Claude + delivery HTTP nodes');
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
assert(serialized.includes("'Bearer ' +"), 'GitHub Authorization uses Bearer expression');

const fetchNodes = workflow.nodes.filter((n) =>
  ['Fetch Commits', 'Fetch Closed Issues', 'Fetch Merged PRs'].includes(n.name),
);
assert(fetchNodes.length === 3, 'has three GitHub fetch nodes');
assert(fetchNodes.every((n) => n.alwaysOutputData === true), 'GitHub fetch nodes always output data (empty week safe)');
assert(
  fetchNodes.every((n) => n.parameters?.options?.response?.response?.responseFormat === 'json'),
  'GitHub fetch nodes parse JSON responses',
);

const loadConfig = workflow.nodes.find((n) => n.name === 'Load Config');
assert(loadConfig?.parameters?.jsCode?.includes('weekStart.toISOString()'), 'Load Config emits ISO8601 weekStart');
assert(loadConfig?.parameters?.jsCode?.includes('weekEnd: now.toISOString()'), 'Load Config emits ISO8601 weekEnd');

const commitsFetch = workflow.nodes.find((n) => n.name === 'Fetch Commits');
const issuesFetch = workflow.nodes.find((n) => n.name === 'Fetch Closed Issues');
const prsFetch = workflow.nodes.find((n) => n.name === 'Fetch Merged PRs');
const sinceFromConfig = "$('Load Config').first().json.weekStart";
assert(
  commitsFetch?.parameters?.queryParameters?.parameters?.some(
    (p) => p.name === 'since' && p.value?.includes(sinceFromConfig),
  ),
  'Fetch Commits filters by Load Config weekStart',
);
assert(
  issuesFetch?.parameters?.queryParameters?.parameters?.some(
    (p) => p.name === 'since' && p.value?.includes(sinceFromConfig),
  ),
  'Fetch Closed Issues filters by Load Config weekStart',
);
assert(
  prsFetch?.parameters?.queryParameters?.parameters?.some(
    (p) => p.name === 'q' && p.value?.includes('weekStart.slice(0, 10)'),
  ),
  'Fetch Merged PRs search query uses Load Config weekStart date',
);

const mergeNode = workflow.nodes.find((n) => n.name === 'Merge GitHub Results');
assert(mergeNode?.parameters?.mode === 'append', 'Merge GitHub Results uses append mode (sync barrier for parallel fetches)');

const buildPrompt = workflow.nodes.find((n) => n.name === 'Build Claude Prompt');
assert(buildPrompt?.parameters?.jsCode?.includes('merged_at'), 'filters merged PRs by date');
assert(buildPrompt?.parameters?.mode === 'runOnceForAllItems', 'Build Claude Prompt runs once after merge');
assert(buildPrompt?.parameters?.jsCode?.includes('collectRecords'), 'collects all GitHub HTTP items');
assert(buildPrompt?.parameters?.jsCode?.includes('rows[0].items'), 'unwraps GitHub search API responses');
assert(buildPrompt?.parameters?.jsCode?.includes('system:'), 'Claude request includes system prompt');
assert(buildPrompt?.parameters?.jsCode?.includes('JSON.stringify(activity'), 'sends structured activity JSON to Claude');
assert(
  buildPrompt?.parameters?.jsCode?.includes("language === 'FR'"),
  'Build Claude Prompt switches system instructions for FR language',
);

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

if (failures.length) {
  console.error('FAILED:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log(`OK: ${workflow.nodes.length} nodes, all acceptance checks passed.`);
