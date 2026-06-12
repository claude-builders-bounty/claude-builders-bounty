import { test, describe } from "node:test";
import { strict as assert } from "node:assert";
import { parseReviewOutput, buildReviewPrompt } from "../src/review.js";
import { formatMarkdown, formatJson } from "../src/format.js";
import { mockReview } from "../src/mock.js";
import type { PullRequest } from "../src/fetch-pr.js";

const SAMPLE_PR: PullRequest = {
  title: "feat(api): add /v2/users endpoint",
  author: "alice",
  baseRef: "main",
  headRef: "feat/users-v2",
  body: "Adds a versioned users endpoint with cursor pagination.",
  diff: [
    "diff --git a/src/api/users.ts b/src/api/users.ts",
    "index 1234567..89abcde 100644",
    "--- a/src/api/users.ts",
    "+++ b/src/api/users.ts",
    "@@ -1,5 +1,12 @@",
    "+import { safeEval } from 'node:vm'; // TODO: remove",
    "+const x = (computeUser() as any);",
    "+// FIXME: this catches everything",
    "+try { doStuff(); } catch (e) {}",
    "+console.log('users endpoint hit');",
    "+@ts-ignore",
    "+const y = eval(input);",
    " export function listUsers() { return []; }",
  ].join("\n"),
  url: "https://github.com/example/repo/pull/42",
};

describe("parseReviewOutput", () => {
  test("parses well-formed output", () => {
    const out = parseReviewOutput(
      [
        "## Summary",
        "Adds a v2 users endpoint with cursor pagination.",
        "",
        "## Risks",
        "- The cursor logic in src/api/users.ts:42 may produce duplicate pages under load.",
        "- The auth check is bypassed when the X-Internal header is set.",
        "",
        "## Improvements",
        "- Add a unit test for the empty-result case.",
        "",
        "## Confidence",
        "Medium — the diff is small but I noticed the X-Internal bypass in passing.",
      ].join("\n"),
      SAMPLE_PR,
    );

    assert.equal(out.summary, "Adds a v2 users endpoint with cursor pagination.");
    assert.equal(out.risks.length, 2);
    assert.equal(out.improvements.length, 1);
    assert.equal(out.confidence, "Medium");
    assert.equal(out.source.kind, "claude");
    assert.equal(out.context.prUrl, SAMPLE_PR.url);
  });

  test("collapses 'None identified' into empty list", () => {
    const out = parseReviewOutput(
      "## Summary\nX\n\n## Risks\n- None identified.\n\n## Improvements\n- None.\n\n## Confidence\nHigh\n",
      SAMPLE_PR,
    );
    assert.deepEqual(out.risks, []);
    assert.deepEqual(out.improvements, []);
    assert.equal(out.confidence, "High");
  });

  test("defaults missing Confidence to Low", () => {
    const out = parseReviewOutput("## Summary\nX\n", SAMPLE_PR);
    assert.equal(out.confidence, "Low");
  });

  test("preserves multiline bullets", () => {
    const out = parseReviewOutput(
      "## Summary\nAdds users.\n\n## Risks\n- First risk.\n- Second risk.\n- Third risk.\n\n## Improvements\n- One.\n\n## Confidence\nLow\n",
      SAMPLE_PR,
    );
    assert.deepEqual(out.risks, ["First risk.", "Second risk.", "Third risk."]);
    assert.deepEqual(out.improvements, ["One."]);
  });
});

describe("buildReviewPrompt", () => {
  test("includes title, author, and diff", () => {
    const prompt = buildReviewPrompt(SAMPLE_PR);
    assert.match(prompt.user, /Title: feat\(api\): add \/v2\/users endpoint/);
    assert.match(prompt.user, /Author: alice/);
    assert.match(prompt.user, /URL: https:\/\/github\.com\/example\/repo\/pull\/42/);
    assert.match(prompt.user, /Base: main\s+Head: feat\/users-v2/);
    assert.match(prompt.user, /```diff/);
  });
});

describe("formatMarkdown", () => {
  test("renders all four sections in order", () => {
    const out = formatMarkdown({
      summary: "Adds users.",
      risks: ["Risk 1."],
      improvements: ["Improve 1."],
      confidence: "Medium",
      source: { kind: "claude" },
      context: { prTitle: "x", prUrl: "y", diffLines: 100 },
    });

    const sections = ["## Summary", "## Risks", "## Improvements", "## Confidence"];
    const indices = sections.map((s) => out.indexOf(s));
    assert.deepEqual(indices.slice().sort((a, b) => a - b), indices);
    assert.ok(out.indexOf("Risk 1.") > 0);
    assert.ok(out.indexOf("Improve 1.") > 0);
    assert.match(out, /Medium —/);
  });

  test("emits 'None identified' for empty lists", () => {
    const out = formatMarkdown({
      summary: "x",
      risks: [],
      improvements: [],
      confidence: "Low",
      source: { kind: "claude" },
      context: { prTitle: "x", prUrl: "y", diffLines: 10 },
    });
    assert.match(out, /## Risks\n\n- None identified\./);
    assert.match(out, /## Improvements\n\n- None identified\./);
  });

  test("mock source adds heuristic rationale to confidence line", () => {
    const out = formatMarkdown({
      summary: "x",
      risks: [],
      improvements: [],
      confidence: "Low",
      source: { kind: "mock" },
      context: { prTitle: "x", prUrl: "y", diffLines: 10 },
    });
    assert.match(out, /Heuristic mock reviewer/);
  });
});

describe("formatJson", () => {
  test("emits a parseable JSON envelope", () => {
    const out = formatJson({
      summary: "x",
      risks: ["a"],
      improvements: ["b"],
      confidence: "High",
      source: { kind: "claude", model: "claude-sonnet-4-20250514" },
      context: { prTitle: "t", prUrl: "u", diffLines: 5 },
    });
    const parsed = JSON.parse(out);
    assert.equal(parsed.confidence, "High");
    assert.equal(parsed.risks[0], "a");
  });
});

describe("mockReview", () => {
  test("flags the heuristic anti-patterns in SAMPLE_PR", () => {
    const out = mockReview(SAMPLE_PR);
    assert.equal(out.source.kind, "mock");
    assert.equal(out.confidence, "Low");
    // The sample diff contains: TODO, FIXME, as any, @ts-ignore, eval(),
    // empty catch, and console.log — all should be flagged.
    const joined = out.risks.join("\n");
    assert.match(joined, /TODO/);
    assert.match(joined, /FIXME/);
    assert.match(joined, /as any/);
    assert.match(joined, /@ts-ignore/);
    assert.match(joined, /eval\(\)/);
    assert.match(joined, /Empty catch/);
    assert.match(joined, /console/);
  });

  test("always emits improvements even on a clean diff", () => {
    const clean: PullRequest = { ...SAMPLE_PR, diff: "diff --git a/x b/x\n@@ -1 +1 @@\n-x\n+y\n" };
    const out = mockReview(clean);
    assert.equal(out.risks.length, 0);
    assert.ok(out.improvements.length >= 2);
  });
});
