const test = require('node:test');
const assert = require('node:assert/strict');
const { parseDiff, analyzeDiff, formatMarkdownReview } = require('../pr_reviewer.js');

const sampleDiff = `diff --git a/src/auth.js b/src/auth.js
index 1234567..89abcdef 100644
--- a/src/auth.js
+++ b/src/auth.js
@@ -1,5 +1,6 @@
 const express = require('express');
+const API_SECRET = "sk_live_1234567890abcdef";
 
 function login(req, res) {
+  const query = "SELECT * FROM users WHERE email = '" + req.body.email + "'";
   return res.json({ success: true });
 }
`;

test('parseDiff accurately counts additions and files', () => {
  const files = parseDiff(sampleDiff);
  assert.equal(files.length, 1);
  assert.equal(files[0].file, 'src/auth.js');
  assert.equal(files[0].additions, 2);
});

test('analyzeDiff flags hardcoded secrets and sql injection risks', () => {
  const files = parseDiff(sampleDiff);
  const analysis = analyzeDiff(files);
  
  assert.ok(analysis.risks.some(r => r.includes('hardcoded credential')));
  assert.ok(analysis.risks.some(r => r.includes('SQL string interpolation')));
  assert.ok(analysis.suggestions.length > 0);
});

test('formatMarkdownReview renders structured Keep-a-Changelog compatible markdown', () => {
  const files = parseDiff(sampleDiff);
  const analysis = analyzeDiff(files);
  const output = formatMarkdownReview(analysis, { url: 'https://github.com/org/repo/pull/42' });

  assert.ok(output.includes('Summary of Changes'));
  assert.ok(output.includes('Identified Risks'));
  assert.ok(output.includes('Improvement Suggestions'));
  assert.ok(output.includes('Reviewer Confidence Score'));
});
