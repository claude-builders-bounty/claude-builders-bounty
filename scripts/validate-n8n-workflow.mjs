import { readFileSync } from 'node:fs';
import { basename } from 'node:path';

const workflowPath = new URL('../workflows/n8n-weekly-dev-summary.json', import.meta.url);
const readmePath = new URL('../README-n8n-weekly-dev-summary.md', import.meta.url);

const workflow = JSON.parse(readFileSync(workflowPath, 'utf8'));
const readme = readFileSync(readmePath, 'utf8');

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const nodes = workflow.nodes || [];
const nodeByName = new Map(nodes.map((node) => [node.name, node]));
const types = new Set(nodes.map((node) => node.type));
const serialized = JSON.stringify(workflow);

assert(workflow.name === 'Weekly GitHub Dev Summary with Claude', 'Workflow name changed unexpectedly.');
assert(types.has('n8n-nodes-base.scheduleTrigger'), 'Missing weekly schedule trigger.');
assert(types.has('n8n-nodes-base.manualTrigger'), 'Missing manual test trigger.');
assert(types.has('n8n-nodes-base.httpRequest'), 'Missing HTTP Request nodes.');
assert(nodeByName.has('Fetch Commits'), 'Missing GitHub commits request.');
assert(nodeByName.has('Fetch Closed Issues'), 'Missing GitHub closed issues request.');
assert(nodeByName.has('Fetch Merged Pull Requests'), 'Missing GitHub merged pull requests request.');
assert(nodeByName.has('Claude Messages API'), 'Missing Claude API request node.');
assert(nodeByName.has('Send Slack or Discord Webhook'), 'Missing destination webhook request node.');
assert(serialized.includes('claude-sonnet-4-20250514'), 'Claude Sonnet 4 model is not configured.');
assert(serialized.includes('GITHUB_OWNER'), 'Repository owner must be configurable.');
assert(serialized.includes('GITHUB_REPO'), 'Repository name must be configurable.');
assert(serialized.includes('DESTINATION_WEBHOOK_URL'), 'Destination webhook must be configurable.');
assert(serialized.includes('SUMMARY_LANGUAGE'), 'Language must be configurable.');

const schedule = nodeByName.get('Weekly Friday Trigger')?.parameters?.rule?.interval?.[0];
assert(schedule?.field === 'weeks', 'Schedule trigger must run weekly.');
assert(schedule?.triggerAtHour === 17, 'Schedule trigger must run at 17:00.');

const setupSteps = [...readme.matchAll(/^\d+\. /gm)];
assert(setupSteps.length > 0 && setupSteps.length <= 5, 'README setup must be five steps or fewer.');

console.log(`Validated ${basename(workflowPath.pathname)} with ${nodes.length} nodes and ${setupSteps.length} setup steps.`);
