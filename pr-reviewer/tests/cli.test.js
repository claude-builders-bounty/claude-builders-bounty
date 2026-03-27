import test from 'node:test';
import assert from 'node:assert/strict';
import { parseArgs, parsePrUrl, renderReview, heuristicAnalyze } from '../src/main.js';

test('returns usage without --pr', () => {
  assert.equal(parseArgs([]).error, 'Usage: claude-review --pr <github-pr-url>');
});

test('parses --pr argument', () => {
  assert.equal(parseArgs(['--pr', 'https://github.com/octo/repo/pull/1']).prUrl, 'https://github.com/octo/repo/pull/1');
});

test('parses github pr url', () => {
  assert.deepEqual(parsePrUrl('https://github.com/octo/repo/pull/123'), { repo: 'octo/repo', number: '123' });
});

test('renders structured markdown', () => {
  const pr = {
    title: 'Add webhook retries',
    url: 'https://github.com/octo/repo/pull/1',
    author: { login: 'octocat' },
    changedFiles: 1,
    files: [{ path: 'src/webhook.js' }],
  };
  const analysis = heuristicAnalyze({ additions: 10, deletions: 2, files: [{ path: 'src/webhook.js' }] }, '');
  const out = renderReview({ pr, diffText: 'diff --git', analysis, repo: 'octo/repo' });
  assert.match(out, /## Summary/);
  assert.match(out, /## Risks/);
  assert.match(out, /## Improvement Suggestions/);
  assert.match(out, /## Confidence/);
});
