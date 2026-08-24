import test from "node:test";
import assert from "node:assert/strict";
import { parsePrUrl, analyzeDiff, generateMarkdownReview } from "../pr_reviewer.js";

test("parsePrUrl extracts owner, repo, and pull number correctly", () => {
  const result = parsePrUrl("https://github.com/Build-Africa-DAO/baraza-protocol/pull/55");
  assert.deepEqual(result, {
    owner: "Build-Africa-DAO",
    repo: "baraza-protocol",
    pullNumber: "55"
  });
});

test("analyzeDiff flags potential hardcoded secrets and large diffs", () => {
  const sampleDiff = `
diff --git a/src/auth.ts b/src/auth.ts
--- a/src/auth.ts
+++ b/src/auth.ts
@@ -1,3 +1,4 @@
+const api_key = "12345-secret-value";
+try { doSomething(); } catch (e) {}
`;
  const analysis = analyzeDiff(sampleDiff);
  assert.equal(analysis.filesCount, 1);
  assert.ok(analysis.risks.some(r => r.includes("credentials") || r.includes("secret")));
  assert.ok(analysis.risks.some(r => r.includes("Empty catch block")));
});

test("generateMarkdownReview produces structured Markdown with confidence score", () => {
  const analysis = {
    filesCount: 2,
    addedCount: 45,
    removedCount: 12,
    risks: ["No critical security or runtime risks detected in the analyzed diff chunk."],
    suggestions: ["Code structure adheres to standard project conventions."],
    confidence: "High"
  };

  const md = generateMarkdownReview(analysis, { title: "Test PR", url: "https://github.com/owner/repo/pull/1" });
  assert.ok(md.includes("## 🤖 Claude Code Review: Test PR"));
  assert.ok(md.includes("### 📝 Summary of Changes"));
  assert.ok(md.includes("### ⚠️ Identified Risks"));
  assert.ok(md.includes("### 💡 Improvement Suggestions"));
  assert.ok(md.includes("**High Confidence**"));
});
