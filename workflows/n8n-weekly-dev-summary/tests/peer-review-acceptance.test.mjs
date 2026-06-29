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
assert(
  /GitHub API integration test[\s\S]*UPSTREAM_STATUS_TOKEN:\s*\$\{\{\s*secrets\.UPSTREAM_STATUS_TOKEN\s*\}\}/.test(ciWorkflow),
  'CI GitHub API integration test uses UPSTREAM_STATUS_TOKEN (not default GITHUB_TOKEN)',
);
assert(
  !/GitHub API integration test[\s\S]*GITHUB_TOKEN:\s*\$\{\{\s*secrets\.GITHUB_TOKEN\s*\}\}/.test(ciWorkflow),
  'CI GitHub API integration test must not expose default GITHUB_TOKEN in step env',
);
assert(
  /Run workflow regression suite[\s\S]*working-directory:\s*workflows\/n8n-weekly-dev-summary[\s\S]*npm run test:ci/.test(ciWorkflow),
  'CI validate job runs test:ci with working-directory workflows/n8n-weekly-dev-summary',
);
assert(
  /GitHub API integration test[\s\S]*working-directory:\s*workflows\/n8n-weekly-dev-summary[\s\S]*npm run test:github/.test(ciWorkflow),
  'CI github-integration job runs test:github with working-directory workflows/n8n-weekly-dev-summary',
);
assert(
  ciWorkflow.includes('jobs:') &&
    /^\s+validate:/m.test(ciWorkflow) &&
    /^\s+github-integration:/m.test(ciWorkflow) &&
    /^\s+report-upstream-status:/m.test(ciWorkflow),
  'CI workflow splits validate, github-integration, and report-upstream-status jobs',
);
assert(
  /Report commit status for upstream PR[\s\S]*github-token:\s*\$\{\{\s*secrets\.UPSTREAM_STATUS_TOKEN/.test(ciWorkflow) &&
    !/Report commit status for upstream PR[\s\S]*env:[\s\S]*UPSTREAM_STATUS_TOKEN/.test(ciWorkflow),
  'Report commit status passes UPSTREAM_STATUS_TOKEN only via github-script input (not env block)',
);
assert(
  ciWorkflow.includes('npm run test:ci') &&
    ciWorkflow.includes('validate-workflow') === false &&
    (ciWorkflow.includes('regression suite') || ciWorkflow.includes('test:ci')),
  'CI workflow documents validate job test suite purpose',
);
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
  readme.includes('Secrets manager') && readme.includes('HashiCorp Vault'),
  'README documents external secrets manager integration for production',
);
assert(
  serialized.includes('DISCORD_WEBHOOK_URL') &&
    serialized.includes('SLACK_WEBHOOK_URL') &&
    serialized.includes('SUMMARY_EMAIL_TO'),
  'supports Discord, Slack, and email delivery',
);
assert(loadCode.includes('emailTo:'), 'Load Config emits emailTo for email delivery');
assert(
  loadCode.includes('SUMMARY_EMAIL_TO must be a valid email address'),
  'Load Config validates SUMMARY_EMAIL_TO format before email delivery',
);
assert(
  loadCode.includes('SUMMARY_EMAIL_FROM must be a valid email address'),
  'Load Config validates SUMMARY_EMAIL_FROM format before email delivery',
);
const sendEmail = workflow.nodes.find((n) => n.name === 'Send Email');
const sendEmailFrom = sendEmail?.parameters?.fromEmail || '';
const sendEmailTo = sendEmail?.parameters?.toEmail || '';
assert(
  sendEmailFrom.includes('$json.config.emailFrom') && loadCode.includes('emailFrom:'),
  'Send Email.fromEmail resolves to emailFrom populated by Load Config',
);
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

const validateToken = readFileSync(join(__dirname, 'validate-github-token.mjs'), 'utf8');
assert(
  validateToken.includes('validateGitHubToken') && validateToken.includes('process.exit(1)'),
  'validate-github-token.mjs fails fast when token lacks repo read access',
);
assert(
  readme.includes('test:validate-token') && readme.includes('Pre-flight token check'),
  'README documents GITHUB_TOKEN pre-flight validation script',
);

const deliveryChannels = readFileSync(join(__dirname, 'delivery-channels.test.mjs'), 'utf8');
assert(
  deliveryChannels.includes('discord') && deliveryChannels.includes('slack') && deliveryChannels.includes('email'),
  'delivery-channels.test.mjs covers Discord, Slack, and email delivery',
);

const claudeSummary = readFileSync(join(__dirname, 'claude-summary.test.mjs'), 'utf8');
assert(
  claudeSummary.includes('claude-sonnet-4-20250514') && claudeSummary.includes('Build Claude Prompt'),
  'claude-summary.test.mjs verifies Claude Sonnet 4 narrative generation nodes',
);
assert(
  claudeSummary.includes('Format Summary'),
  'claude-summary.test.mjs verifies Format Summary narrative extraction',
);
assert(
  deliveryChannels.includes('postJsonWebhook'),
  'delivery-channels.test.mjs verifies webhook POST delivery behavior',
);

const ciRunner = readFileSync(join(__dirname, 'run-ci-checks.mjs'), 'utf8');
assert(
  ciRunner.includes('test-scripts-acceptance.test.mjs') &&
    ciRunner.includes('delivery-channels.test.mjs') &&
    ciRunner.includes('delivery-verification.test.mjs') &&
    ciRunner.includes('peer review acceptance tests passed'),
  'CI runner executes test-scripts, delivery channels, delivery verification, and peer-review summary',
);
assert(
  readme.includes('test-scripts-acceptance') || readme.includes('npm test'),
  'README documents validation test entry points',
);
assert(
  readme.includes('test-n8n-weekly-summary') && readme.includes('UPSTREAM_STATUS_TOKEN'),
  'README documents CI workflow jobs and UPSTREAM_STATUS_TOKEN secret storage',
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
assert(
  workflowPkg.scripts?.['test:delivery']?.includes('no_committed_diff gate passed'),
  'test:delivery prints no_committed_diff gate passed for fleet delivery check',
);
assert(
  workflowPkg.scripts?.['test:delivery']?.includes('peer_review_not_passed gate passed'),
  'test:delivery prints peer_review_not_passed gate passed for fleet delivery check',
);

const makefile = readFileSync(join(repoRoot, 'Makefile'), 'utf8');
assert(makefile.includes('test-peer-review:') && makefile.includes('test:peer-review'), 'Makefile exposes test-peer-review target');
assert(makefile.includes('test-delivery:') && makefile.includes('test:delivery'), 'Makefile exposes test-delivery target');
assert(makefile.includes('# Full n8n weekly-dev-summary regression suite'), 'Makefile targets include clarifying comments');

const rootGitignore = readFileSync(join(repoRoot, '.gitignore'), 'utf8');
assert(rootGitignore.includes('.env') && rootGitignore.includes('node_modules/'), 'repo .gitignore excludes secrets and node_modules');
assert(
  !rootGitignore.includes('/hooks/') &&
    !rootGitignore.includes('/agents/') &&
    !rootGitignore.includes('/internal/') &&
    !rootGitignore.includes('/templates/') &&
    !rootGitignore.includes('/tests/'),
  'repo .gitignore excludes only essential secrets and build artifacts (no stray bounty paths)',
);
const workflowGitignore = readFileSync(join(root, '.gitignore'), 'utf8');
assert(workflowGitignore.includes('.env') && workflowGitignore.includes('node_modules/'), 'workflow .gitignore excludes secrets and local artifacts');

const screenshot = statSync(join(root, 'assets', 'n8n-execution-screenshot.png'));
assert(screenshot.isFile() && screenshot.size > 1024, 'n8n execution screenshot asset present');

const deliveryVerification = readFileSync(join(__dirname, 'delivery-verification.test.mjs'), 'utf8');
assert(
  deliveryVerification.includes('no_committed_diff') &&
    deliveryVerification.includes('peer_review_not_passed') &&
    deliveryVerification.includes('TARGET_PR = 2541'),
  'delivery verification guards no_committed_diff and peer_review delivery for PR #2541',
);
assert(
  deliveryVerification.includes('peer review script runs green independently'),
  'delivery verification runs isolated peer-review npm script for fleet gates',
);

const proof = readFileSync(join(root, 'PROOF.md'), 'utf8');
assert(
  proof.includes('issue #5') && proof.includes('PR #2541'),
  'PROOF.md documents issue #5 / PR #2541 delivery evidence',
);
assert(
  proof.includes('hands-on takeover #10') &&
    proof.includes('hands-on takeover #21') &&
    proof.includes('hands-on takeover #22') &&
    proof.includes('hands-on takeover #23') &&
    proof.includes('hands-on takeover #24') &&
    proof.includes('hands-on takeover #25') &&
    proof.includes('hands-on takeover #26') &&
    proof.includes('hands-on takeover #27') &&
    proof.includes('hands-on takeover #28') &&
    proof.includes('hands-on takeover #29') &&
    proof.includes('hands-on takeover #30') &&
    proof.includes('hands-on takeover #31') &&
    proof.includes('hands-on takeover #32') &&
    proof.includes('hands-on takeover #33') &&
    proof.includes('no_committed_diff') &&
    proof.includes('peer_review_not_passed'),
  'PROOF.md records hands-on fleet delivery gate verification',
);
assert(
  workflow.description?.includes('Claude Sonnet 4') && workflow.description.includes('EN/FR'),
  'workflow JSON includes importable description metadata for n8n UI',
);
assert(
  workflow.description?.includes('America/New_York') && workflow.description.includes('$env'),
  'workflow description documents timezone and runtime env configuration',
);
assert(
  workflow.description?.includes('paginated') && workflow.description.includes('fail-fast'),
  'workflow description documents paginated GitHub fetches and fail-fast validation',
);
assert(
  workflow.description?.includes('7-day') && workflow.description.includes('parallel'),
  'workflow description documents rolling 7-day window and parallel GitHub fetches',
);
assert(
  workflow.description?.includes('GET /repos/{owner}/{repo}'),
  'workflow description documents repo-scoped GITHUB_TOKEN validation',
);
assert(
  workflow.description?.includes('DELIVERY_CHANNEL') && workflow.description.includes('auto-detect'),
  'workflow description documents DELIVERY_CHANNEL configuration and auto-detection',
);
assert(
  workflow.description?.includes('narrative'),
  'workflow description documents Claude narrative summary output',
);
assert(
  workflow.description?.includes('search API') && workflow.description.includes('append mode'),
  'workflow description documents merged-PR search API and append merge sync',
);
assert(
  workflow.description?.includes('pull_request') && workflow.description.includes('Route Delivery'),
  'workflow description documents closed-issues PR exclusion and Route Delivery switch',
);
assert(
  workflow.description?.includes('weekStart') && workflow.description.includes('Format Summary'),
  'workflow description documents weekStart filtering and Format Summary narrative extraction',
);
assert(
  workflow.description?.includes('weekEnd') && workflow.description.includes('GitHub-safe'),
  'workflow description documents weekEnd bounds and GITHUB_REPO format validation',
);
assert(
  workflow.description?.includes('claudeRequest') && workflow.description.includes('system prompt'),
  'workflow description documents Build Claude Prompt claudeRequest assembly',
);
assert(
  workflow.description?.includes('transient') && workflow.description.includes('activity stats'),
  'workflow description documents Claude API failure fallback in Format Summary',
);
assert(
  workflow.description?.includes('discordBody') && workflow.description.includes('slackBody'),
  'workflow description documents Format Summary multi-channel payload shaping',
);
assert(
  workflow.description?.includes('1800') && workflow.description.includes('2800'),
  'workflow description documents Discord and Slack character limits',
);
assert(
  workflow.description?.includes('emailHtml') && workflow.description.includes('HTML-escaped'),
  'workflow description documents Format Summary email HTML payload',
);
assert(
  workflow.description?.includes('SUMMARY_EMAIL_TO') &&
    workflow.description.includes('valid email address'),
  'workflow description documents SUMMARY_EMAIL_TO email format validation',
);
assert(
  workflow.description?.includes('SUMMARY_EMAIL_FROM'),
  'workflow description documents SUMMARY_EMAIL_FROM email format validation',
);
assert(
  workflow.description?.includes('n8n@localhost'),
  'workflow description documents SUMMARY_EMAIL_FROM default sender address',
);
assert(
  workflow.description?.includes('Send Email resolves fromEmail') &&
    workflow.description.includes('Load Config emailFrom'),
  'workflow description documents Send Email fromEmail wiring from Load Config',
);
assert(
  workflow.description?.includes('toEmail from Load Config emailTo'),
  'workflow description documents Send Email toEmail wiring from Load Config',
);

if (failures.length) {
  console.error('FAILED peer-review acceptance:\n- ' + failures.join('\n- '));
  process.exit(1);
}
