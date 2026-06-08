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
assert(serialized.includes('claude-sonnet-4-20250514'), 'uses required Claude model');
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

const setupSteps = [...readme.matchAll(/^### \d+\./gm)];
assert(setupSteps.length > 0 && setupSteps.length <= 5, 'README setup in five steps or fewer');

const screenshot = statSync(join(root, 'assets', 'n8n-execution-screenshot.png'));
assert(screenshot.isFile() && screenshot.size > 1024, 'n8n execution screenshot asset present');

if (failures.length) {
  console.error('FAILED peer-review acceptance:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log(`OK: ${failures.length === 0 ? 'all' : 0} peer-review acceptance checks passed (${workflow.nodes.length} nodes).`);
