#!/usr/bin/env node
/**
 * Regression test for GitHub response collection (n8n splits arrays into items).
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { collectRecords, isGitHubError } from './lib/github-collect.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const workflow = JSON.parse(
  readFileSync(join(__dirname, '..', 'weekly-dev-summary.json'), 'utf8'),
);

const loadConfig = workflow.nodes.find((n) => n.name === 'Load Config');
const buildPrompt = workflow.nodes.find((n) => n.name === 'Build Claude Prompt');
const code = buildPrompt?.parameters?.jsCode || '';
const loadCode = loadConfig?.parameters?.jsCode || '';

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

assert(
  loadCode.includes('weekStart.toISOString()') && loadCode.includes('weekEnd: now.toISOString()'),
  'Load Config emits ISO8601 week boundaries for GitHub since filters',
);
assert(
  loadCode.includes('validateGitHubToken') && loadCode.includes('api.github.com/repos/'),
  'Load Config validates GITHUB_TOKEN via GET /repos/{owner}/{repo} before repo API calls',
);
assert(!loadCode.includes('api.github.com/user'), 'Load Config does not use /user token validation');
assert(
  !loadCode.includes('githubToken:') && !loadCode.includes('anthropicApiKey:'),
  'Load Config does not copy secrets into item JSON',
);
assert(
  buildPrompt?.parameters?.mode === 'runOnceForAllItems',
  'Build Claude Prompt runs once after merge (avoids duplicate Claude calls)',
);
assert(code.includes('collectRecords'), 'uses collectRecords helper for GitHub nodes');
assert(code.includes('isGitHubError'), 'collectRecords rejects GitHub error payloads');
assert(code.includes('item.records'), 'reads paginated records from GitHub fetch nodes');
assert(code.includes('throw new Error'), 'collectRecords fails fast on missing node output');

for (const name of ['Fetch Commits', 'Fetch Closed Issues', 'Fetch Merged PRs']) {
  const fetchCode = workflow.nodes.find((n) => n.name === name)?.parameters?.jsCode || '';
  assert(fetchCode.includes('fetchGitHubPages'), `${name} paginates GitHub API responses`);
  assert(fetchCode.includes('per_page: \'100\''), `${name} requests 100 items per page`);
  assert(fetchCode.includes('$env.GITHUB_TOKEN'), `${name} reads GITHUB_TOKEN from env only`);
  assert(!fetchCode.includes('continueRegularOutput'), `${name} does not swallow HTTP errors`);
}

assert(isGitHubError({ message: 'Not Found', documentation_url: 'https://docs.github.com' }), 'detects GitHub error objects');
assert(!isGitHubError({ sha: 'abc', commit: { message: 'fix' } }), 'accepts commit records');

const errorRejected = collectRecords([{ json: { records: [
  { sha: 'good', commit: { author: { date: '2026-06-01T12:00:00Z' }, message: 'ok' } },
  { message: 'rate limit', documentation_url: 'https://docs.github.com' },
] } }]);
assert(errorRejected.length === 1 && errorRejected[0].sha === 'good', 'collectRecords filters GitHub error objects');

const weekStart = new Date('2026-05-30T00:00:00Z');
const weekEnd = new Date('2026-06-06T23:59:59Z');
const inWeek = (iso) => {
  if (!iso) return false;
  const d = new Date(iso);
  return d >= weekStart && d <= weekEnd;
};
const emptyWeek = {
  commits: collectRecords([]).filter((c) => inWeek(c.commit?.author?.date)),
  issues: collectRecords([]).filter((i) => inWeek(i.closed_at)),
  prs: collectRecords([]).filter((p) => inWeek(p.merged_at)),
};
assert(
  emptyWeek.commits.length === 0 &&
    emptyWeek.issues.length === 0 &&
    emptyWeek.prs.length === 0,
  'empty GitHub responses yield zero activity records',
);
assert(
  code.includes('commits.length') && code.includes('closedIssues') && code.includes('mergedPullRequests'),
  'prompt builder references all three activity buckets (quiet weeks included)',
);

const mergeNode = workflow.nodes.find((n) => n.name === 'Merge GitHub Results');
assert(mergeNode?.parameters?.mode === 'append', 'merge node uses append (not mergeByPosition) for uneven branch sizes');

const claude = workflow.nodes.find((n) => n.name === 'Claude API');
assert(claude?.onError === 'continueRegularOutput', 'Claude API continues on transient failures');
const formatCode = workflow.nodes.find((n) => n.name === 'Format Summary')?.parameters?.jsCode || '';
assert(formatCode.includes('Claude API unavailable'), 'Format Summary provides fallback when Claude fails');

if (failures.length) {
  console.error('FAILED:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log('OK: GitHub data collection handles n8n item splitting.');
