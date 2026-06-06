#!/usr/bin/env node
/**
 * Regression tests for weekly-dev-summary n8n workflow JSON.
 * Run: node tests/validate-workflow.mjs
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const workflowPath = join(__dirname, '..', 'weekly-dev-summary.json');
const workflow = JSON.parse(readFileSync(workflowPath, 'utf8'));

const failures = [];

function assert(condition, message) {
  if (!condition) failures.push(message);
}

const nodeTypes = workflow.nodes.map((n) => n.type);
const nodeNames = workflow.nodes.map((n) => n.name);

assert(workflow.name, 'workflow has a name');
assert(Array.isArray(workflow.nodes) && workflow.nodes.length >= 8, 'workflow has enough nodes');
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
assert(serialized.includes('SUMMARY_LANGUAGE'), 'configurable language EN/FR');
assert(serialized.includes('DISCORD_WEBHOOK_URL') || serialized.includes('SLACK_WEBHOOK_URL'), 'webhook delivery configured');
assert(serialized.includes('api.github.com'), 'fetches GitHub API');
assert(serialized.includes('/commits'), 'fetches commits');
assert(serialized.includes('/issues'), 'fetches issues');
assert(serialized.includes('/pulls'), 'fetches pull requests');
assert(serialized.includes('api.anthropic.com/v1/messages'), 'calls Claude API');

const buildPrompt = workflow.nodes.find((n) => n.name === 'Build Claude Prompt');
assert(buildPrompt?.parameters?.jsCode?.includes('merged_at'), 'filters merged PRs by date');
assert(buildPrompt?.parameters?.mode === 'runOnceForAllItems', 'Build Claude Prompt runs once after merge');
assert(buildPrompt?.parameters?.jsCode?.includes('collectRecords'), 'collects all GitHub HTTP items');

const connections = Object.keys(workflow.connections || {});
assert(connections.includes('Friday 5pm Weekly Trigger'), 'trigger is wired');
assert(connections.includes('Claude API'), 'Claude node is wired');

if (failures.length) {
  console.error('FAILED:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log(`OK: ${workflow.nodes.length} nodes, all acceptance checks passed.`);
