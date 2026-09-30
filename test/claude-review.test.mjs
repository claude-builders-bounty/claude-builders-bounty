import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import {
  applyFileLimit,
  analyzePullRequest,
  formatMarkdown,
  parseArgs,
  parsePullRequestUrl,
} from "../bin/claude-review.mjs";

const fixture = {
  ref: {
    owner: "example",
    repo: "app",
    number: 42,
    url: "https://github.com/example/app/pull/42",
  },
  pr: {
    number: 42,
    title: "Add billing webhook",
    user: { login: "octocat" },
  },
  files: [
    {
      filename: "app/api/billing/route.ts",
      additions: 80,
      deletions: 12,
      patch: "+const token = process.env.STRIPE_WEBHOOK_SECRET;\n+export async function POST() {}",
    },
    {
      filename: "tests/billing-webhook.test.ts",
      additions: 45,
      deletions: 0,
      patch: "+test('handles webhook', () => {})",
    },
    {
      filename: ".github/workflows/review.yml",
      additions: 22,
      deletions: 0,
      patch: "+permissions:\n+  pull-requests: write",
    },
  ],
};

test("parses GitHub PR URLs", () => {
  assert.deepEqual(
    parsePullRequestUrl("https://github.com/acme/project/pull/123"),
    {
      owner: "acme",
      repo: "project",
      number: 123,
      url: "https://github.com/acme/project/pull/123",
    }
  );
});

test("parses max-files option", () => {
  assert.deepEqual(
    parseArgs(["--pr", "https://github.com/acme/project/pull/123", "--max-files", "10"]),
    {
      pr: "https://github.com/acme/project/pull/123",
      format: "markdown",
      "max-files": 10,
    }
  );
});

test("analyzes diff metadata into required review sections", () => {
  const review = analyzePullRequest(fixture);

  assert.equal(review.pullRequest.title, "Add billing webhook");
  assert.equal(review.stats.changedFiles, 3);
  assert.equal(review.stats.testFiles, 1);
  assert.equal(review.confidence, "Medium");
  assert.match(review.risks.join("\n"), /workflow files changed/i);
  assert.match(review.risks.join("\n"), /credential-like terms/i);
});

test("detects shell code and shell test files", () => {
  const review = analyzePullRequest({
    ref: {
      owner: "example",
      repo: "hooks",
      number: 7,
      url: "https://github.com/example/hooks/pull/7",
    },
    pr: {
      number: 7,
      title: "Add command hook",
      user: { login: "hook-author" },
    },
    files: [
      {
        filename: "hooks/block_destructive_bash.sh",
        additions: 30,
        deletions: 0,
        patch: "+case \"$1\" in rm*) exit 2;; esac",
      },
      {
        filename: "hooks/test_block_destructive_bash.sh",
        additions: 20,
        deletions: 0,
        patch: "+bash hooks/block_destructive_bash.sh",
      },
    ],
  });

  assert.equal(review.stats.codeFiles, 2);
  assert.equal(review.stats.testFiles, 1);
});

test("formats structured markdown review", () => {
  const markdown = formatMarkdown(analyzePullRequest(fixture));

  assert.match(markdown, /^# Claude PR Review/);
  assert.match(markdown, /## Summary/);
  assert.match(markdown, /## Identified Risks/);
  assert.match(markdown, /## Improvement Suggestions/);
  assert.match(markdown, /## Confidence: Medium/);
});

test("bundled real PR samples include required review sections", async () => {
  const samplePaths = [
    "sample-outputs/claude-builders-2271.md",
    "sample-outputs/claude-builders-2277.md",
    "sample-outputs/claude-builders-2284.md",
  ];

  assert.equal(samplePaths.length, 3);

  for (const samplePath of samplePaths) {
    const markdown = await readFile(samplePath, "utf8");

    assert.match(markdown, /^# Claude PR Review/);
    assert.match(markdown, /## Summary/);
    assert.match(markdown, /## Identified Risks/);
    assert.match(markdown, /## Improvement Suggestions/);
    assert.match(markdown, /## Confidence: (Low|Medium|High)/);
  }
});

test("detects extensionless executables from their shebang", () => {
  const review = analyzePullRequest({
    ref: {
      owner: "example",
      repo: "tools",
      number: 8,
      url: "https://github.com/example/tools/pull/8",
    },
    pr: {
      number: 8,
      title: "Add review CLI",
      user: { login: "cli-author" },
    },
    files: [
      {
        filename: "claude-review",
        additions: 3,
        deletions: 0,
        patch: "+#!/usr/bin/env python3\n+import subprocess\n+print('review')",
      },
    ],
  });

  assert.equal(review.stats.codeFiles, 1);
  assert.match(review.summary[0], /application code/i);
  assert.match(review.risks.join("\n"), /without matching test files/i);
});

test("preserves upstream coverage gaps when max-files limits the local pass", () => {
  const input = {
    ref: fixture.ref,
    pr: { ...fixture.pr, truncatedFiles: 7 },
    files: Array.from({ length: 5 }, (_, index) => ({
      filename: `src/file-${index}.js`,
      additions: 1,
      deletions: 0,
      patch: "+export default true;",
    })),
  };

  const limited = applyFileLimit(input, 2);

  assert.equal(limited.files.length, 2);
  assert.equal(limited.pr.truncatedFiles, 10);
  assert.equal(input.files.length, 5);
  assert.equal(input.pr.truncatedFiles, 7);
});

test("reports incomplete file coverage as a risk", () => {
  const review = analyzePullRequest({
    ...fixture,
    pr: { ...fixture.pr, truncatedFiles: 3 },
  });

  assert.match(review.risks.join("\n"), /3 changed files were omitted/i);
  assert.match(review.summary.join("\n"), /3 additional changed files were not analyzed/i);
  assert.equal(review.confidence, "Low");
});

test("write-enabled workflow executes only trusted base code", async () => {
  const workflow = await readFile(".github/workflows/claude-review.yml", "utf8");

  assert.match(workflow, /^\s*pull_request_target:/m);
  assert.match(workflow, /ref:\s*\$\{\{\s*github\.event\.pull_request\.base\.sha\s*\}\}/);
  assert.match(workflow, /actions\/checkout@11bd71901bbe5b1630ceea73d27597364c9af683/);
  assert.match(workflow, /actions\/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020/);
  assert.match(workflow, /actions\/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea/);
  assert.match(workflow, /persist-credentials:\s*false/);
  assert.doesNotMatch(workflow, /github\.event\.pull_request\.(head|merge_commit_sha)/);
  assert.doesNotMatch(workflow, /^\s*pull_request:\s*$/m);
});

test("incomplete file coverage cannot produce high confidence or invent its cause", () => {
  const review = analyzePullRequest({
    ...fixture,
    pr: { ...fixture.pr, truncatedFiles: 1 },
    files: [fixture.files[1]],
  });
  assert.equal(review.confidence, "Low");
  assert.doesNotMatch(review.summary.join("\n"), /because --max-files was set/);
  assert.doesNotMatch(review.risks.join("\n"), /omitted by the configured file limit/);
});

test("missing changed-line patches are disclosed and lower confidence", () => {
  const review = analyzePullRequest({
    ...fixture,
    files: [{ filename: "tests/large.test.js", additions: 20, deletions: 0 }],
  });
  assert.equal(review.confidence, "Low");
  assert.equal(review.stats.missingPatches, 1);
  assert.match(review.risks.join("\n"), /patch text.*unavailable/i);
  assert.match(review.suggestions.join("\n"), /full diff/i);
});

test("metadata-only changes do not falsely report missing changed-line patches", () => {
  const review = analyzePullRequest({
    ...fixture,
    files: [{ filename: "tests/renamed.test.js", status: "renamed", additions: 0, deletions: 0 }],
  });
  assert.equal(review.stats.missingPatches, 0);
  assert.doesNotMatch(review.risks.join("\n"), /patch text.*unavailable/i);
});

test('rejects malformed file limits instead of silently reducing review coverage', () => {
  for (const value of ['1.5', '2files', '1e3', '0x10', '9007199254740993', '0', '-1']) {
    assert.throws(() => parseArgs(['--fixture', 'sample.json', '--max-files', value]), /positive integer/, value);
  }
  assert.equal(parseArgs(['--fixture', 'sample.json', '--max-files', '25'])['max-files'], 25);
});
