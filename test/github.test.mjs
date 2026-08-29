import test from 'node:test';
import assert from 'node:assert/strict';
import { parsePullRequestUrl, reviewCommentBody, truncateUnifiedDiff } from '../src/github.mjs';

test('parsePullRequestUrl parses a canonical GitHub PR URL', () => {
  assert.deepEqual(parsePullRequestUrl('https://github.com/openai/example/pull/42'), {
    owner: 'openai',
    repo: 'example',
    number: 42,
    htmlUrl: 'https://github.com/openai/example/pull/42',
  });
});

test('parsePullRequestUrl rejects non-PR URLs', () => {
  assert.throws(
    () => parsePullRequestUrl('https://github.com/openai/example/issues/42'),
    /Expected a GitHub pull request URL/,
  );
});

test('truncateUnifiedDiff preserves a small diff', () => {
  const value = 'diff --git a/a.js b/a.js\n+hello\n';
  const result = truncateUnifiedDiff(value, 2_000);
  assert.equal(result.truncated, false);
  assert.equal(result.diff, value);
});

test('truncateUnifiedDiff bounds oversized input and marks truncation', () => {
  const first = `diff --git a/a.js b/a.js\n${'+x\n'.repeat(700)}`;
  const second = `diff --git a/b.js b/b.js\n${'+y\n'.repeat(700)}`;
  const result = truncateUnifiedDiff(first + second, 2_100);
  assert.equal(result.truncated, true);
  assert.ok(result.diff.length <= 2_100);
  assert.match(result.diff, /DIFF TRUNCATED/);
});

test('reviewCommentBody contains a stable hidden marker', () => {
  const body = reviewCommentBody('## Summary\nOkay');
  assert.match(body, /<!-- claude-pr-reviewer-bounty -->/);
  assert.match(body, /## Summary/);
});
