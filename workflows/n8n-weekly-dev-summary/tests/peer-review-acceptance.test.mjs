#!/usr/bin/env node
/**
 * Peer-review acceptance cases for bounty #5 (issue #5).
 * Codifies manual review checklist so regressions fail CI.
 */
import { readFileSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const workflow = JSON.parse(readFileSync(join(root, 'weekly-dev-summary.json'), 'utf8'));
const readme = readFileSync(join(root, 'README.md'), 'utf8');
const serialized = JSON.stringify(workflow);

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

// Issue #5 acceptance criteria
assert(workflow.nodes?.length >= 8, 'exportable n8n workflow with sufficient nodes');
assert(serialized.includes('scheduleTrigger'), 'weekly cron trigger present');

const trigger = workflow.nodes.find((n) => n.type === 'n8n-nodes-base.scheduleTrigger');
const interval = trigger?.parameters?.rule?.interval?.[0];
assert(interval?.field === 'weeks' && interval?.triggerAtDay?.includes(5) && interval?.triggerAtHour === 17,
  'trigger runs weekly on Friday at 5pm');

assert(serialized.includes('/commits') && serialized.includes('/issues') && serialized.includes('search/issues'),
  'fetches commits, closed issues, and merged PRs from GitHub API');
assert(serialized.includes('api.anthropic.com/v1/messages'), 'calls Claude Messages API');
assert(serialized.includes('claude-sonnet-4-20250514'), 'uses required Claude model');
assert(
  workflow.nodes.some((n) => n.name === 'Claude API' && n.type === 'n8n-nodes-base.httpRequest'),
  'Claude API node posts to Anthropic',
);

const loadConfig = workflow.nodes.find((n) => n.name === 'Load Config');
assert(
  loadConfig?.parameters?.jsCode?.includes('GitHub-safe characters only'),
  'Load Config validates GITHUB_REPO format before API calls',
);
assert(
  serialized.includes('DISCORD_WEBHOOK_URL') &&
    serialized.includes('SLACK_WEBHOOK_URL') &&
    serialized.includes('SUMMARY_EMAIL_TO'),
  'supports Discord, Slack, and email delivery',
);
assert(
  serialized.includes('GITHUB_REPO') &&
    serialized.includes('DELIVERY_CHANNEL') &&
    serialized.includes('SUMMARY_LANGUAGE'),
  'configurable repo, channel, and EN/FR language',
);

const buildPrompt = workflow.nodes.find((n) => n.name === 'Build Claude Prompt');
const buildCode = buildPrompt?.parameters?.jsCode || '';
assert(buildCode.includes("language === 'FR'"), 'FR language branch in prompt builder');
assert(
  buildCode.includes('Rédigez un résumé') && buildCode.includes('résumez l'),
  'FR user and system instructions localized',
);
assert(buildCode.includes('!i.pull_request'), 'closed issues filter excludes pull requests');
assert(buildCode.includes('system:') && buildCode.includes('claudeRequest'), 'Claude request includes system prompt');

const connections = workflow.connections || {};
function targets(source, index = 0) {
  return (connections[source]?.main?.[index] || []).map((edge) => edge.node);
}
const pipeline = [
  ['Friday 5pm Weekly Trigger', 'Load Config'],
  ['Load Config', 'Fetch Commits'],
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

const setupSteps = [...readme.matchAll(/^### \d+\./gm)];
assert(setupSteps.length > 0 && setupSteps.length <= 5, 'README setup in five steps or fewer');

const screenshot = statSync(join(root, 'assets', 'n8n-execution-screenshot.png'));
assert(screenshot.isFile() && screenshot.size > 1024, 'n8n execution screenshot asset present');

if (failures.length) {
  console.error('FAILED peer-review acceptance:\n- ' + failures.join('\n- '));
  process.exit(1);
}
