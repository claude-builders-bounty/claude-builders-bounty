import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const workflowDir = path.join(root, 'workflows', 'n8n-weekly-dev-summary-email');
const workflowPath = path.join(workflowDir, 'weekly-dev-summary-email.workflow.json');
const readmePath = path.join(workflowDir, 'README.md');

assert.ok(existsSync(workflowPath), 'workflow JSON must exist');
assert.ok(existsSync(readmePath), 'README must exist');

const workflow = JSON.parse(await readFile(workflowPath, 'utf8'));
const readme = await readFile(readmePath, 'utf8');

assert.equal(workflow.name, 'Weekly GitHub Dev Summary - Claude + Email');
assert.equal(workflow.active, false, 'export should be inactive by default');
assert.ok(Array.isArray(workflow.nodes), 'workflow nodes must be an array');
assert.ok(workflow.nodes.length >= 8, 'workflow should contain the full pipeline');

const nodeByName = new Map(workflow.nodes.map((node) => [node.name, node]));
for (const name of [
  'Manual Test Trigger',
  'Friday 5 PM Weekly Trigger',
  'Read Environment Config',
  'Build Weekly Config',
  'Fetch Commits',
  'Fetch Closed Issues',
  'Fetch Merged PRs',
  'Build Claude Request',
  'Generate Claude Summary',
  'Prepare Email Payload',
  'Send Email Summary',
]) {
  assert.ok(nodeByName.has(name), `missing node: ${name}`);
}

const schedule = nodeByName.get('Friday 5 PM Weekly Trigger');
assert.equal(schedule.type, 'n8n-nodes-base.scheduleTrigger');
assert.match(JSON.stringify(schedule.parameters), /0\s+17\s+\*\s+\*\s+5/, 'schedule must run Friday at 5pm');

const manual = nodeByName.get('Manual Test Trigger');
assert.equal(manual.type, 'n8n-nodes-base.manualTrigger');

const envConfig = JSON.stringify(nodeByName.get('Read Environment Config').parameters);
assert.match(envConfig, /GITHUB_REPO/);
assert.match(envConfig, /DESTINATION_EMAIL/);
assert.match(envConfig, /SUMMARY_LANGUAGE/);
assert.match(envConfig, /EN/);
assert.match(envConfig, /FR/);

for (const node of workflow.nodes.filter((candidate) => candidate.type === 'n8n-nodes-base.code')) {
  const code = node.parameters.jsCode;
  assert.ok(!code.includes('$env'), `${node.name} Code node must not read env directly`);
  assert.ok(!code.includes('fetch('), `${node.name} Code node must not depend on fetch`);
}

const commits = nodeByName.get('Fetch Commits');
assert.equal(commits.type, 'n8n-nodes-base.httpRequest');
assert.equal(commits.alwaysOutputData, true, 'zero-commit weeks must still continue');
assert.match(JSON.stringify(commits.parameters), /api\.github\.com/);
assert.match(JSON.stringify(commits.parameters), /commits/);
assert.match(JSON.stringify(commits.parameters), /GITHUB_TOKEN/);

const closedIssues = nodeByName.get('Fetch Closed Issues');
assert.equal(closedIssues.type, 'n8n-nodes-base.httpRequest');
assert.match(JSON.stringify(closedIssues.parameters), /is:issue/);

const mergedPrs = nodeByName.get('Fetch Merged PRs');
assert.equal(mergedPrs.type, 'n8n-nodes-base.httpRequest');
assert.match(JSON.stringify(mergedPrs.parameters), /is:pr/);
assert.match(JSON.stringify(mergedPrs.parameters), /is:merged/);

const claudeRequestCode = nodeByName.get('Build Claude Request').parameters.jsCode;
assert.match(claudeRequestCode, /filter\(\(commit\) => commit\.sha \|\| commit\.commit\)/);

const claude = nodeByName.get('Generate Claude Summary');
assert.equal(claude.type, 'n8n-nodes-base.httpRequest');
assert.equal(claude.parameters.url, 'https://api.anthropic.com/v1/messages');
assert.match(JSON.stringify(claude.parameters), /claude-sonnet-4-20250514/);
assert.match(JSON.stringify(claude.parameters), /ANTHROPIC_API_KEY/);

const email = nodeByName.get('Send Email Summary');
assert.equal(email.type, 'n8n-nodes-base.httpRequest');
assert.match(JSON.stringify(email.parameters), /api\.resend\.com\/emails/);
assert.match(JSON.stringify(email.parameters), /RESEND_API_KEY/);

const connections = workflow.connections ?? {};
assert.ok(connections['Manual Test Trigger'], 'manual trigger must connect to workflow');
assert.ok(connections['Friday 5 PM Weekly Trigger'], 'schedule trigger must connect to workflow');
assert.ok(connections['Send Email Summary'] === undefined, 'final node should not connect onward');

const stepMatches = [...readme.matchAll(/^\d+\.\s+/gm)];
assert.ok(stepMatches.length > 0, 'README must have numbered setup steps');
assert.ok(stepMatches.length <= 5, 'README setup must be five steps or fewer');
for (const term of [
  'GITHUB_REPO',
  'DESTINATION_EMAIL',
  'SUMMARY_LANGUAGE',
  'ANTHROPIC_API_KEY',
  'RESEND_API_KEY',
  'claude-sonnet-4-20250514',
  'successful-execution.jpg',
]) {
  assert.match(readme, new RegExp(term), `README must document ${term}`);
}

console.log('weekly dev summary workflow validation passed');
