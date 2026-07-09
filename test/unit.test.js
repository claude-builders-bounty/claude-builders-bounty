const assert = require("node:assert/strict");
const { parseDiffFiles, parsePullRequestUrl } = require("../src/github");
const { createHeuristicReview, REQUIRED_HEADINGS } = require("../src/review");

const parsed = parsePullRequestUrl("https://github.com/example/project/pull/123");
assert.deepEqual(parsed, {
  owner: "example",
  repo: "project",
  number: 123,
  htmlUrl: "https://github.com/example/project/pull/123",
});

assert.throws(
  () => parsePullRequestUrl("https://github.com/example/project/issues/123"),
  /Expected a URL/,
);

const files = parseDiffFiles(`diff --git a/src/index.js b/src/index.js
index 1111111..2222222 100644
--- a/src/index.js
+++ b/src/index.js
@@ -1,2 +1,2 @@
-old line
+new line
 context
diff --git a/test/index.test.js b/test/index.test.js
new file mode 100644
--- /dev/null
+++ b/test/index.test.js
@@ -0,0 +1,2 @@
+test one
+test two
`);

assert.deepEqual(files, [
  {
    filename: "src/index.js",
    status: "modified",
    additions: 1,
    deletions: 1,
    changes: 2,
  },
  {
    filename: "test/index.test.js",
    status: "added",
    additions: 2,
    deletions: 0,
    changes: 2,
  },
]);

const review = createHeuristicReview({
  htmlUrl: "https://github.com/example/project/pull/123",
  title: "Add feature",
  author: "contributor",
  baseRef: "main",
  headRef: "feature",
  changedFiles: 2,
  additions: 42,
  deletions: 7,
  files: [
    {
      filename: "src/review.js",
      status: "modified",
      additions: 30,
      deletions: 5,
      changes: 35,
    },
    {
      filename: "test/review.test.js",
      status: "added",
      additions: 12,
      deletions: 2,
      changes: 14,
    },
  ],
  diff: "diff --git a/src/review.js b/src/review.js\n",
});

for (const heading of REQUIRED_HEADINGS) {
  assert.ok(review.includes(heading), `missing heading: ${heading}`);
}
assert.match(review, /High|Medium|Low/);

console.log("unit tests passed");
