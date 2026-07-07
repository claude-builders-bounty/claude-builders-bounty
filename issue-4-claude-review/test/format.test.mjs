import test from "node:test";
import assert from "node:assert/strict";
import { buildReviewPrompt, validateReviewMarkdown } from "../src/lib/format.mjs";
import { clipDiff, parsePullRequestUrl } from "../src/lib/github.mjs";

test("parsePullRequestUrl extracts owner repo and number", () => {
  assert.deepEqual(
    parsePullRequestUrl("https://github.com/openai/openai-node/pull/123"),
    {
      owner: "openai",
      repo: "openai-node",
      number: 123,
      url: "https://github.com/openai/openai-node/pull/123"
    }
  );
});

test("clipDiff marks long diffs as clipped", () => {
  const input = "a".repeat(30);
  const result = clipDiff(input, 20);

  assert.equal(result.clipped, true);
  assert.match(result.diff, /truncated/);
});

test("validateReviewMarkdown accepts the required structure", () => {
  const markdown = `## PR Review

> **PR**: owner/repo#1
> **Title**: Example
> **Author**: @dev

### Summary
Two short sentences.

### Identified Risks
- None found.

### Improvement Suggestions
- Add a regression test.

### Confidence
High
`;

  assert.equal(validateReviewMarkdown(markdown), true);
});

test("buildReviewPrompt includes diff content and metadata", () => {
  const prompt = buildReviewPrompt({
    owner: "owner",
    repo: "repo",
    number: 7,
    title: "Add parser",
    author: "alice",
    baseRef: "main",
    headRef: "feature",
    changedFiles: 2,
    additions: 10,
    deletions: 4,
    url: "https://github.com/owner/repo/pull/7",
    body: "Adds a parser",
    diff: "diff --git a/file b/file"
  });

  assert.match(prompt, /Repository: owner\/repo/);
  assert.match(prompt, /diff --git a\/file b\/file/);
  assert.match(prompt, /### Identified Risks/);
});
