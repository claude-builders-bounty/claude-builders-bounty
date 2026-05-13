import assert from 'node:assert/strict';
import test from 'node:test';
import { createReview } from '../bin/claude-review.js';

test('createReview returns required structured sections', () => {
  const diff = `diff --git a/src/app.js b/src/app.js
index 1111111..2222222 100644
--- a/src/app.js
+++ b/src/app.js
@@ -1,2 +1,3 @@
 export function add(a, b) {
+  if (a == null || b == null) throw new Error('invalid input');
   return a + b;
 }
diff --git a/src/app.test.js b/src/app.test.js
new file mode 100644
--- /dev/null
+++ b/src/app.test.js
@@ -0,0 +1,3 @@
+import { add } from './app.js';
+test('adds', () => {});
+test('rejects missing values', () => {});
`;

  const review = createReview(diff, 'test');

  assert.match(review, /### Summary of Changes/);
  assert.match(review, /### Identified Risks/);
  assert.match(review, /### Improvement Suggestions/);
  assert.match(review, /### Confidence Score/);
  assert.match(review, /High|Medium|Low/);
});

test('createReview flags missing tests', () => {
  const diff = `diff --git a/src/auth.js b/src/auth.js
index 1111111..2222222 100644
--- a/src/auth.js
+++ b/src/auth.js
@@ -1,2 +1,2 @@
-export const role = 'user';
+export const role = 'admin';
`;

  const review = createReview(diff, 'test');

  assert.match(review, /No tests changed/);
  assert.match(review, /Security-sensitive/);
});
