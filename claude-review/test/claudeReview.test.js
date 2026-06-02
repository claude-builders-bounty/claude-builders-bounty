'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');
const {
  analyzeDiff,
  formatReviewMarkdown,
  parseArgs,
  parsePullRequestUrl,
  parseUnifiedDiff
} = require('../src/claudeReview');

const SAMPLE_DIFF = `diff --git a/src/api/user.js b/src/api/user.js
index 1111111..2222222 100644
--- a/src/api/user.js
+++ b/src/api/user.js
@@ -1,4 +1,9 @@
+import fetch from 'node-fetch';
+
 export async function handler(req) {
-  return { ok: true };
+  const token = req.body.token;
+  const response = await fetch('https://example.com/users/' + token);
+  return response.json();
 }
diff --git a/package.json b/package.json
index 3333333..4444444 100644
--- a/package.json
+++ b/package.json
@@ -1,3 +1,4 @@
 {
-  "name": "demo"
+  "name": "demo",
+  "dependencies": { "node-fetch": "^3.0.0" }
 }
`;

test('parsePullRequestUrl extracts owner, repo, and number', () => {
  assert.deepEqual(parsePullRequestUrl('https://github.com/owner/repo/pull/123'), {
    owner: 'owner',
    repo: 'repo',
    number: 123,
    url: 'https://github.com/owner/repo/pull/123'
  });
});

test('parseArgs accepts required CLI options', () => {
  const args = parseArgs([
    '--pr',
    'https://github.com/owner/repo/pull/123',
    '--fixture',
    'fixture.diff',
    '--max-diff-chars',
    '5000'
  ]);

  assert.equal(args.pr, 'https://github.com/owner/repo/pull/123');
  assert.equal(args.fixture, 'fixture.diff');
  assert.equal(args.maxDiffChars, 5000);
});

test('parseUnifiedDiff returns file stats and added lines', () => {
  const files = parseUnifiedDiff(SAMPLE_DIFF);

  assert.equal(files.length, 2);
  assert.equal(files[0].path, 'src/api/user.js');
  assert.equal(files[0].additions, 5);
  assert.equal(files[0].deletions, 1);
  assert.equal(files[1].path, 'package.json');
});

test('formatReviewMarkdown contains required bounty sections', () => {
  const files = parseUnifiedDiff(SAMPLE_DIFF);
  const review = analyzeDiff({
    pr: {
      owner: 'owner',
      repo: 'repo',
      number: 123,
      url: 'https://github.com/owner/repo/pull/123'
    },
    metadata: {
      title: 'Add user API',
      author: 'octocat',
      base: 'main',
      head: 'feature',
      additions: 8,
      deletions: 2,
      changedFiles: 2
    },
    parsedDiff: files,
    diff: SAMPLE_DIFF,
    truncated: false
  });

  const markdown = formatReviewMarkdown(review);

  assert.match(markdown, /## Summary/);
  assert.match(markdown, /## Identified Risks/);
  assert.match(markdown, /## Improvement Suggestions/);
  assert.match(markdown, /## Confidence Score/);
  assert.match(markdown, /\*\*(Low|Medium|High)\*\*/);
  assert.match(markdown, /No test files were detected/);
});
