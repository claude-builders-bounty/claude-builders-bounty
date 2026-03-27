#!/usr/bin/env node

/**
 * Mock-based integration test for claude-review CLI.
 * Tests the full pipeline: URL parsing → GitHub API fetch → formatting.
 * Claude API call is mocked with a realistic response.
 *
 * Run: node test/test.js
 */

import { parsePrUrl, fetchDiff, fetchPrMeta } from "../src/github.js";
import { formatReview } from "../src/formatter.js";
import { strict as assert } from "node:assert";

const PASS = "\x1b[32m✓\x1b[0m";
const FAIL = "\x1b[31m✗\x1b[0m";
let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ${PASS} ${name}`);
    passed++;
  } catch (err) {
    console.log(`  ${FAIL} ${name}`);
    console.log(`    ${err.message}`);
    failed++;
  }
}

async function testAsync(name, fn) {
  try {
    await fn();
    console.log(`  ${PASS} ${name}`);
    passed++;
  } catch (err) {
    console.log(`  ${FAIL} ${name}`);
    console.log(`    ${err.message}`);
    failed++;
  }
}

// ─── URL Parsing Tests ──────────────────────────────────────────
console.log("\n📋 URL Parsing");

test("parses standard PR URL", () => {
  const result = parsePrUrl("https://github.com/facebook/react/pull/32489");
  assert.equal(result.owner, "facebook");
  assert.equal(result.repo, "react");
  assert.equal(result.pullNumber, 32489);
});

test("parses PR URL with trailing slash", () => {
  const result = parsePrUrl("https://github.com/owner/repo/pull/1/");
  assert.equal(result.owner, "owner");
  assert.equal(result.repo, "repo");
  assert.equal(result.pullNumber, 1);
});

test("throws on invalid URL", () => {
  assert.throws(() => parsePrUrl("https://github.com/owner/repo"), /Invalid GitHub PR URL/);
});

test("throws on non-GitHub URL", () => {
  assert.throws(() => parsePrUrl("https://gitlab.com/owner/repo/pull/1"), /Invalid GitHub PR URL/);
});

test("parses complex owner/repo names", () => {
  const result = parsePrUrl("https://github.com/claude-builders-bounty/claude-builders-bounty/pull/89");
  assert.equal(result.owner, "claude-builders-bounty");
  assert.equal(result.repo, "claude-builders-bounty");
  assert.equal(result.pullNumber, 89);
});

// ─── GitHub API Tests (live, read-only) ─────────────────────────
console.log("\n🌐 GitHub API (live fetch)");

await testAsync("fetches PR metadata from real GitHub PR", async () => {
  const meta = await fetchPrMeta("claude-builders-bounty", "claude-builders-bounty", 89);
  assert.ok(meta.title, "should have title");
  assert.ok(meta.author, "should have author");
  assert.ok(typeof meta.additions === "number", "additions should be number");
  assert.ok(typeof meta.deletions === "number", "deletions should be number");
  assert.ok(typeof meta.changedFiles === "number", "changedFiles should be number");
});

await testAsync("fetches PR diff from real GitHub PR", async () => {
  const diff = await fetchDiff("claude-builders-bounty", "claude-builders-bounty", 89);
  assert.ok(diff.length > 100, "diff should be non-trivial");
  assert.ok(diff.includes("diff --git"), "should be a unified diff");
});

// ─── Formatter Tests ────────────────────────────────────────────
console.log("\n📝 Markdown Formatter");

const mockReview = {
  summary: "This PR adds a new caching layer for database queries, reducing response times by ~40%.",
  risks: [
    "Cache invalidation strategy is too aggressive — may serve stale data for up to 5 minutes.",
    "No memory limit on the cache — could cause OOM on high-traffic deployments."
  ],
  suggestions: [
    "Add a configurable TTL with a sensible default (e.g., 60s) in src/cache/config.ts:12",
    "Implement LRU eviction with a max size of 10,000 entries",
    "Add cache hit/miss metrics to the monitoring dashboard"
  ],
  confidence: "Medium",
  confidence_reasoning: "The caching logic is straightforward, but the lack of eviction policy is a concern for production use."
};

const mockMeta = {
  title: "feat: add query caching layer",
  author: "cache-dev",
  head: "feat/query-cache",
  base: "main",
  additions: 234,
  deletions: 18,
  changedFiles: 6
};

test("formats review with all sections", () => {
  const md = formatReview(mockReview, mockMeta, "https://github.com/example/repo/pull/99");
  assert.ok(md.includes("## 📋 PR Review"), "should have review header");
  assert.ok(md.includes("### 📝 Summary"), "should have summary");
  assert.ok(md.includes("### ⚠️ Identified Risks"), "should have risks");
  assert.ok(md.includes("### 💡 Improvement Suggestions"), "should have suggestions");
  assert.ok(md.includes("### 📊 Confidence Score"), "should have confidence");
  assert.ok(md.includes("🟡 Medium"), "should show medium confidence");
  assert.ok(md.includes("@cache-dev"), "should include author");
  assert.ok(md.includes("+234 / -18"), "should include stats");
});

test("formats review with no risks", () => {
  const noRisks = { ...mockReview, risks: [] };
  const md = formatReview(noRisks, mockMeta, "https://github.com/x/y/pull/1");
  assert.ok(md.includes("✅ No significant risks"), "should show no-risks message");
});

test("formats review with high confidence", () => {
  const high = { ...mockReview, confidence: "High" };
  const md = formatReview(high, mockMeta, "https://github.com/x/y/pull/1");
  assert.ok(md.includes("🟢 High"), "should show green circle for high");
});

test("formats review with low confidence", () => {
  const low = { ...mockReview, confidence: "Low" };
  const md = formatReview(low, mockMeta, "https://github.com/x/y/pull/1");
  assert.ok(md.includes("🔴 Low"), "should show red circle for low");
});

// ─── Results ────────────────────────────────────────────────────
console.log(`\n${"─".repeat(40)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
