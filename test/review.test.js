import assert from "node:assert/strict";
import { test } from "node:test";
import { reviewPullRequestDiff } from "../src/review.js";

test("returns required structured markdown sections", () => {
  const diff = [
    "diff --git a/src/auth.js b/src/auth.js",
    "index 1111111..2222222 100644",
    "--- a/src/auth.js",
    "+++ b/src/auth.js",
    "@@ -1,2 +1,3 @@",
    "-const token = req.headers.authorization;",
    "+const token = req.headers.authorization?.replace('Bearer ', '');",
    "+console.log('auth token changed');"
  ].join("\n");

  const review = reviewPullRequestDiff(diff, { source: "fixture" });

  assert.match(review, /## Summary/);
  assert.match(review, /## Identified Risks/);
  assert.match(review, /## Improvement Suggestions/);
  assert.match(review, /## Confidence Score: (Low|Medium|High)/);
  assert.match(review, /Authentication or authorization paths changed/);
});
