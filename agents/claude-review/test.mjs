import assert from "node:assert/strict";
import { analyzeDiff, buildReview, parsePullRequestUrl, renderReview } from "./claude-review.mjs";

const parsed = parsePullRequestUrl("https://github.com/example/repo/pull/123");
assert.deepEqual(parsed, { owner: "example", repo: "repo", number: 123 });

const diff = `diff --git a/src/payments.ts b/src/payments.ts
index 1111111..2222222 100644
--- a/src/payments.ts
+++ b/src/payments.ts
@@ -1,3 +1,4 @@
 export function pay() {
-  return "old";
+  const token = process.env.PAYMENT_TOKEN;
+  // payment confirmation path
+  return token ? "new" : "missing";
 }
diff --git a/README.md b/README.md
index 3333333..4444444 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Demo
+Updated usage.
`;

const stats = analyzeDiff(diff);
assert.equal(stats.added, 4);
assert.equal(stats.removed, 1);
assert.equal(stats.fileList.length, 2);

const metadata = {
  number: 123,
  title: "Improve payment flow",
  body: "",
  base: {
    repo: {
      full_name: "example/repo",
    },
  },
};

const review = buildReview(metadata, diff);
const markdown = renderReview(review);

assert.match(markdown, /## Summary/);
assert.match(markdown, /## Identified Risks/);
assert.match(markdown, /## Improvement Suggestions/);
assert.match(markdown, /## Confidence/);
assert.match(markdown, /Authentication, authorization, or payment-adjacent logic/);
assert.equal(review.confidence, "Medium");

console.log("claude-review tests passed");
