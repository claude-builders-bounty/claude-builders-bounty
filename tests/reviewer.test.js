import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { reviewDiff, summarizeDiff } from "../src/reviewer.js";

const sample = fs.readFileSync("tests/fixtures/sample-pr.diff", "utf8");

test("summarizes files, additions, deletions, and test coverage", () => {
  const stats = summarizeDiff(sample);
  assert.equal(stats.filesChanged, 2);
  assert.equal(stats.testsTouched, true);
  assert.equal(stats.additions, 7);
});

test("returns structured markdown-ready review fields", () => {
  const review = reviewDiff(sample, { source: "fixture" });
  assert.match(review.summary, /changes 2 file/);
  assert.equal(Array.isArray(review.risks), true);
  assert.equal(Array.isArray(review.suggestions), true);
  assert.match(review.confidence, /Low|Medium|High/);
});
