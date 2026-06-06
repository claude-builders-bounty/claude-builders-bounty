import assert from "node:assert/strict";
import { analyzePullRequest, parsePullRequestUrl, renderMarkdown } from "../bin/claude-review.mjs";

assert.deepEqual(parsePullRequestUrl("https://github.com/owner/repo/pull/123"), {
  owner: "owner",
  repo: "repo",
  pullNumber: 123
});

assert.throws(() => parsePullRequestUrl("https://example.com/nope"), /PR URL/);

const diff = `diff --git a/package.json b/package.json
index 111..222 100644
--- a/package.json
+++ b/package.json
@@ -1,3 +1,4 @@
 {
+  "scripts": { "test": "node test.js" },
   "private": true
 }
diff --git a/.github/workflows/review.yml b/.github/workflows/review.yml
new file mode 100644
--- /dev/null
+++ b/.github/workflows/review.yml
@@ -0,0 +1,2 @@
+permissions:
+  contents: read
`;

const analysis = analyzePullRequest({
  title: "Add workflow and package metadata",
  body: "",
  files: ["package.json", ".github/workflows/review.yml"],
  diff
});

assert.equal(analysis.confidence, "High");
assert.match(analysis.summary, /changes 2 files/);
assert.ok(analysis.risks.some((risk) => risk.includes("Workflow changes")));
assert.ok(analysis.risks.some((risk) => risk.includes("Dependency or package metadata")));

const markdown = renderMarkdown({ prUrl: "https://github.com/owner/repo/pull/123", analysis });
assert.match(markdown, /### Summary/);
assert.match(markdown, /### Identified Risks/);
assert.match(markdown, /### Improvement Suggestions/);
assert.match(markdown, /### Confidence Score/);

console.log("claude-review tests passed");
