import { strict as assert } from "node:assert";
import { buildReview } from "../src/review.mjs";

const fixture = {
  url: "https://github.com/example/project/pull/7",
  owner: "example",
  repo: "project",
  number: 7,
  title: "Improve settings validation",
  body: "Adds stricter validation around settings and documents the expected behavior.",
  state: "open",
  author: "contributor",
  base: "main",
  head: "settings-validation",
  additions: 42,
  deletions: 10,
  changedFiles: 3,
  files: [
    {
      filename: "src/settings.ts",
      status: "modified",
      additions: 30,
      deletions: 8,
      changes: 38,
      patch: "validate settings before save",
    },
    {
      filename: "src/settings.test.ts",
      status: "modified",
      additions: 10,
      deletions: 2,
      changes: 12,
      patch: "adds validation coverage",
    },
    {
      filename: "README.md",
      status: "modified",
      additions: 2,
      deletions: 0,
      changes: 2,
      patch: "document settings validation",
    },
  ],
};

const review = buildReview(fixture);

assert.match(review, /## Summary/);
assert.match(review, /## Identified Risks/);
assert.match(review, /## Improvement Suggestions/);
assert.match(review, /## Changed Files/);
assert.match(review, /## Confidence/);
assert.match(review, /src\/settings\.ts/);
assert.match(review, /src\/settings\.test\.ts/);

console.log("review.test.mjs ok");

