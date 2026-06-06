#!/usr/bin/env node
/**
 * Regression tests for n8n-weekly-dev-summary workflow JSON.
 * Run: node workflows/tests/validate-workflow.mjs
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const workflowPath = join(__dirname, '..', 'n8n-weekly-dev-summary.json');
const workflow = JSON.parse(readFileSync(workflowPath, 'utf8'));

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

const nodeTypes = workflow.nodes.map((n) => n.type);
const nodeNames = workflow.nodes.map((n) => n.name);

assert(workflow.name, 'workflow has a name');
assert(workflow.nodes.length >= 9, 'workflow has enough nodes');
assert(nodeTypes.includes('n8n-nodes-base.scheduleTrigger'), 'has schedule trigger');
assert(nodeNames.includes('Merge GitHub Results'), 'merges parallel GitHub fetches');
assert(nodeNames.includes('Generate Summary with Claude'), 'has Claude API node');

const trigger = workflow.nodes.find((n) => n.type === 'n8n-nodes-base.scheduleTrigger');
const interval = trigger?.parameters?.rule?.interval?.[0];
assert(interval?.field === 'weeks', 'trigger runs weekly');
assert(interval?.triggerAtDay?.includes(5), 'trigger runs on Friday');
assert(interval?.triggerAtHour === 17, 'trigger runs at 5pm');

const serialized = JSON.stringify(workflow);
assert(serialized.includes('claude-sonnet-4-20250514'), 'uses required Claude model');
assert(serialized.includes('GITHUB_REPO'), 'configurable GitHub repo');
assert(serialized.includes('SUMMARY_LANGUAGE'), 'configurable language EN/FR');
assert(serialized.includes('DISCORD_WEBHOOK_URL'), 'Discord webhook delivery configured');
assert(serialized.includes('api.github.com'), 'fetches GitHub API');
assert(serialized.includes('/commits'), 'fetches commits');
assert(serialized.includes('/issues'), 'fetches issues');
assert(serialized.includes('/pulls'), 'fetches pull requests');
assert(serialized.includes('api.anthropic.com/v1/messages'), 'calls Claude API');

const fetchNodes = workflow.nodes.filter((n) =>
  ['Fetch Commits', 'Fetch Closed Issues', 'Fetch Closed Pull Requests'].includes(n.name),
);
assert(fetchNodes.length === 3, 'has three GitHub fetch nodes');
assert(fetchNodes.every((n) => n.alwaysOutputData === true), 'GitHub fetch nodes always output data');

const mergeNode = workflow.nodes.find((n) => n.name === 'Merge GitHub Results');
assert(mergeNode?.parameters?.mode === 'append', 'merge node waits for all GitHub fetches');
assert(mergeNode?.parameters?.numberInputs === 3, 'merge node has three inputs');

const buildRequest = workflow.nodes.find((n) => n.name === 'Build Claude Request');
assert(buildRequest?.parameters?.mode === 'runOnceForAllItems', 'Build Claude Request runs once after merge');
assert(buildRequest?.parameters?.jsCode?.includes('collectRecords'), 'collects all GitHub HTTP items');
assert(buildRequest?.parameters?.jsCode?.includes('merged_at'), 'filters merged PRs by date');

if (failures.length) {
  console.error('FAILED:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log(`OK: ${workflow.nodes.length} nodes, all acceptance checks passed.`);
