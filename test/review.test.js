const assert = require("node:assert/strict");
const { describe, it } = require("node:test");

const {
  analyzeDiff,
  parsePullRequestUrl,
  renderMarkdownReview
} = require("../src/review");

const fixtureDiff = [
  "diff --git a/src/index.js b/src/index.js",
  "index 1111111..2222222 100644",
  "--- a/src/index.js",
  "+++ b/src/index.js",
  "@@ -1,2 +1,3 @@",
  " const value = 1;",
  "+export const next = value + 1;",
  "diff --git a/test/index.test.js b/test/index.test.js",
  "new file mode 100644",
  "--- /dev/null",
  "+++ b/test/index.test.js",
  "@@ -0,0 +1,2 @@",
  "+const assert = require('node:assert/strict');",
  "+assert.equal(2, 2);"
].join("\n");

describe("parsePullRequestUrl", () => {
  it("parses a GitHub pull request URL", () => {
    assert.deepEqual(
      parsePullRequestUrl("https://github.com/owner/repo/pull/123"),
      {
        owner: "owner",
        repo: "repo",
        number: "123",
        diffUrl: "https://github.com/owner/repo/pull/123.diff",
        url: "https://github.com/owner/repo/pull/123"
      }
    );
  });

  it("rejects non-GitHub pull request URLs", () => {
    assert.throws(() => parsePullRequestUrl("https://example.com/pr/1"), /GitHub pull request URL/);
  });
});

describe("analyzeDiff", () => {
  it("summarizes changed files, stats, risks, and confidence", () => {
    const review = analyzeDiff(fixtureDiff, {
      url: "https://github.com/owner/repo/pull/123"
    });

    assert.equal(review.stats.files, 2);
    assert.equal(review.stats.additions, 3);
    assert.equal(review.stats.deletions, 0);
    assert.equal(review.confidence, "High");
    assert.deepEqual(review.files, ["src/index.js", "test/index.test.js"]);
    assert.match(renderMarkdownReview(review), /### Confidence score: High/);
  });

  it("recognizes Python test modules", () => {
    const diff = [
      "diff --git a/src/app.py b/src/app.py",
      "--- a/src/app.py",
      "+++ b/src/app.py",
      "@@ -1 +1 @@",
      "-value = 1",
      "+value = 2",
      "diff --git a/test_app.py b/test_app.py",
      "--- /dev/null",
      "+++ b/test_app.py",
      "@@ -0,0 +1 @@",
      "+assert True"
    ].join("\n");

    const review = analyzeDiff(diff);

    assert.equal(review.confidence, "High");
    assert.equal(
      review.risks.includes("No test files were detected in the diff, so behavior may be under-covered."),
      false
    );
  });
});
