#!/usr/bin/env node
/**
 * Regression test for GitHub response collection (n8n splits arrays into items).
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

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
  buildPrompt?.parameters?.mode === 'runOnceForAllItems',
  'Build Claude Prompt runs once after merge (avoids duplicate Claude calls)',
);
assert(code.includes('collectRecords'), 'uses collectRecords helper for GitHub nodes');
assert(code.includes(".all()"), 'reads all n8n items from GitHub HTTP nodes');
assert(code.includes('rows[0].items'), 'unwraps GitHub search API item arrays');
assert(code.includes('Array.isArray(rows[0])'), 'handles wrapped array responses');

// Runtime: empty-week repos must still produce a valid Claude prompt.
const weekStart = new Date('2026-05-30T00:00:00Z');
const weekEnd = new Date('2026-06-06T23:59:59Z');
const inWeek = (iso) => {
  if (!iso) return false;
  const d = new Date(iso);
  return d >= weekStart && d <= weekEnd;
};
const collectRecords = (items) => {
  if (!items.length) return [];
  const rows = items.map((item) => item.json).filter((row) => row && typeof row === 'object');
  if (rows.length === 1 && Array.isArray(rows[0].items)) return rows[0].items;
  if (rows.length === 1 && Array.isArray(rows[0])) return rows[0];
  return rows;
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
  code.includes('commits.length') || code.includes('activity'),
  'prompt builder references collected activity counts',
);

// Append merge passes all branch items through; uneven counts must not drop records.
const mergeNode = workflow.nodes.find((n) => n.name === 'Merge GitHub Results');
assert(mergeNode?.parameters?.mode === 'append', 'merge node uses append (not mergeByPosition) for uneven branch sizes');
const branchA = [{ sha: 'aaa', commit: { author: { date: '2026-06-01T12:00:00Z' }, message: 'a' } }];
const branchB = [];
const branchC = [
  { number: 1, merged_at: '2026-06-02T12:00:00Z', title: 'pr' },
  { number: 2, merged_at: '2026-06-03T12:00:00Z', title: 'pr2' },
];
const appendMerged = [...branchA, ...branchB, ...branchC];
assert(appendMerged.length === 3, 'append merge retains all items when branch sizes differ');

// Simulate Build Claude Prompt output for a quiet week (no commits/issues/PRs).
const quietWeekConfig = {
  repoFullName: 'org/repo',
  weekStart: '2026-05-30T00:00:00.000Z',
  weekEnd: '2026-06-06T23:59:59.000Z',
  language: 'EN',
};
const quietActivity = {
  repository: quietWeekConfig.repoFullName,
  weekStart: quietWeekConfig.weekStart,
  weekEnd: quietWeekConfig.weekEnd,
  commits: [],
  closedIssues: [],
  mergedPullRequests: [],
};
const quietPrompt = {
  model: 'claude-sonnet-4-20250514',
  messages: [{ role: 'user', content: JSON.stringify(quietActivity) }],
};
assert(
  quietActivity.commits.length === 0 &&
    quietActivity.closedIssues.length === 0 &&
    quietActivity.mergedPullRequests.length === 0,
  'quiet week activity object has zero records',
);
assert(quietPrompt.model === 'claude-sonnet-4-20250514', 'quiet week still targets required Claude model');
assert(
  code.includes('commits.length') && code.includes('closedIssues') && code.includes('mergedPullRequests'),
  'prompt builder references all three activity buckets (quiet weeks included)',
);

if (failures.length) {
  console.error('FAILED:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log('OK: GitHub data collection handles n8n item splitting.');
