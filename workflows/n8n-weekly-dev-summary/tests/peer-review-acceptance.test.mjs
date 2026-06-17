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
const repoRoot = join(root, '..', '..');
const workflow = JSON.parse(readFileSync(join(root, 'weekly-dev-summary.json'), 'utf8'));
const readme = readFileSync(join(root, 'README.md'), 'utf8');
const ciWorkflow = readFileSync(
  join(repoRoot, '.github', 'workflows', 'test-n8n-weekly-summary.yml'),
  'utf8',
);
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
const loadCode = loadConfig?.parameters?.jsCode || '';
assert(
  loadCode.includes('GitHub-safe characters only'),
  'Load Config validates GITHUB_REPO format before API calls',
);
assert(
  loadCode.includes('validateGitHubToken') && loadCode.includes('api.github.com/repos/'),
  'Load Config validates GITHUB_TOKEN via GET /repos/{owner}/{repo} before API calls',
);
assert(
  !loadCode.includes('api.github.com/user'),
  'Load Config does not validate GITHUB_TOKEN via /user (Actions token lacks user scope)',
);
assert(
  loadCode.includes('$env.GITHUB_TOKEN') && loadCode.includes('Set GITHUB_TOKEN'),
  'Load Config requires GITHUB_TOKEN from n8n env (no hardcoded token)',
);
assert(
  loadCode.includes('$env.ANTHROPIC_API_KEY') && loadCode.includes('Set ANTHROPIC_API_KEY'),
  'Load Config requires ANTHROPIC_API_KEY from n8n env (no hardcoded key)',
);
assert(
  !loadCode.includes('githubToken:') &&
    !loadCode.includes('anthropicApiKey:') &&
    !loadCode.includes('discordWebhookUrl:') &&
    !loadCode.includes('slackWebhookUrl:'),
  'Load Config keeps secrets out of n8n execution item JSON',
);
assert(
  serialized.includes('$env.ANTHROPIC_API_KEY') &&
    serialized.includes('$env.DISCORD_WEBHOOK_URL') &&
    serialized.includes('$env.SLACK_WEBHOOK_URL'),
  'delivery and Claude nodes read webhook/API secrets from $env only',
);
assert(!ciWorkflow.includes('pull_request_target'), 'CI workflow avoids pull_request_target fork secret exposure');
for (const name of ['Fetch Commits', 'Fetch Closed Issues', 'Fetch Merged PRs']) {
  const node = workflow.nodes.find((n) => n.name === name);
  assert(node?.onError !== 'continueRegularOutput', `${name} fails fast instead of swallowing GitHub HTTP errors`);
}
const fetchCommits = workflow.nodes.find((n) => n.name === 'Fetch Commits');
assert(fetchCommits?.parameters?.jsCode?.includes('fetchGitHubPages'), 'GitHub fetch nodes paginate beyond 100 items');
assert(
  workflow.nodes.find((n) => n.name === 'Claude API')?.onError === 'continueRegularOutput',
  'Claude API continues on transient Anthropic failures',
);
assert(
  readme.includes('Security:') && readme.includes('$env'),
  'README documents secure env var storage and runtime-only secret access',
);
assert(
  serialized.includes('DISCORD_WEBHOOK_URL') &&
    serialized.includes('SLACK_WEBHOOK_URL') &&
    serialized.includes('SUMMARY_EMAIL_TO'),
  'supports Discord, Slack, and email delivery',
);
assert(loadCode.includes('emailTo:'), 'Load Config emits emailTo for email delivery');
const sendEmail = workflow.nodes.find((n) => n.name === 'Send Email');
const sendEmailTo = sendEmail?.parameters?.toEmail || '';
assert(
  sendEmailTo.includes('$json.config.emailTo') && loadCode.includes('emailTo:'),
  'Send Email.toEmail resolves to emailTo populated by Load Config',
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

const ciRunner = readFileSync(join(__dirname, 'run-ci-checks.mjs'), 'utf8');
assert(
  ciRunner.includes('test-scripts-acceptance.test.mjs') &&
    ciRunner.includes('delivery-verification.test.mjs') &&
    ciRunner.includes('peer review acceptance tests passed'),
  'CI runner executes test-scripts, delivery verification, and peer-review summary',
);
assert(
  readme.includes('test-scripts-acceptance') || readme.includes('npm test'),
  'README documents validation test entry points',
);

const workflowPkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
assert(
  workflowPkg.scripts?.['test:peer-review']?.includes('peer-review-acceptance.test.mjs'),
  'package.json exposes isolated test:peer-review entry point',
);
assert(
  workflowPkg.scripts?.['test:delivery']?.includes('delivery-verification.test.mjs'),
  'package.json exposes isolated test:delivery entry point',
);
assert(
  workflowPkg.scripts?.['test:peer-review']?.includes('OK: peer review acceptance tests passed'),
  'test:peer-review prints fleet-expected peer-review summary',
);
assert(
  workflowPkg.scripts?.['test:delivery']?.includes('OK: delivery verification tests passed'),
  'test:delivery prints fleet-expected delivery summary',
);

const makefile = readFileSync(join(repoRoot, 'Makefile'), 'utf8');
assert(makefile.includes('test-peer-review:') && makefile.includes('test:peer-review'), 'Makefile exposes test-peer-review target');
assert(makefile.includes('test-delivery:') && makefile.includes('test:delivery'), 'Makefile exposes test-delivery target');

const screenshot = statSync(join(root, 'assets', 'n8n-execution-screenshot.png'));
assert(screenshot.isFile() && screenshot.size > 1024, 'n8n execution screenshot asset present');

if (failures.length) {
  console.error('FAILED peer-review acceptance:\n- ' + failures.join('\n- '));
  process.exit(1);
}
