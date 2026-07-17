import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeDiff, formatReview, parseGitHubPullRequestUrl } from '../lib/review.js';

const SAMPLE_DIFF = `diff --git a/src/auth.js b/src/auth.js
index 1111111..2222222 100644
--- a/src/auth.js
+++ b/src/auth.js
@@ -1,3 +1,5 @@
-export function login() { return true; }
+export function login(token) {
+  return Boolean(token);
+}
diff --git a/test/auth.test.js b/test/auth.test.js
new file mode 100644
--- /dev/null
+++ b/test/auth.test.js
@@ -0,0 +1 @@
+console.log('test');
`;

test('parses GitHub pull request URLs', () => {
  assert.deepEqual(parseGitHubPullRequestUrl('https://github.com/owner/repo/pull/123'), {
    owner: 'owner',
    repo: 'repo',
    pullNumber: 123
  });
  assert.equal(parseGitHubPullRequestUrl('https://example.com/owner/repo/pull/123'), null);
});

test('analyzes diff into structured review fields', () => {
  const review = analyzeDiff(SAMPLE_DIFF, { source: 'fixture' });
  assert.equal(review.source, 'fixture');
  assert.equal(review.stats.files.length, 2);
  assert.equal(review.confidence, 'High');
  assert.match(review.risks.join('\n'), /authentication|tokens|secrets/i);
  assert.match(review.suggestions.join('\n'), /debug logging/i);
});

test('formats a Markdown review comment', () => {
  const markdown = formatReview(analyzeDiff(SAMPLE_DIFF));
  assert.match(markdown, /## Claude Review/);
  assert.match(markdown, /### Summary/);
  assert.match(markdown, /### Identified Risks/);
  assert.match(markdown, /### Improvement Suggestions/);
  assert.match(markdown, /### Confidence/);
});
