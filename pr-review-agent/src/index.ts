#!/usr/bin/env node
/**
 * pr-review-agent — CLI entry point
 *
 * Usage:
 *   claude-review --pr https://github.com/owner/repo/pull/123
 *   claude-review --pr 123 --repo owner/repo
 *   claude-review --diff ./my-pr.diff
 *   GITHUB_TOKEN=xxx CLAUDE_API_KEY=xxx claude-review --pr 123 --repo owner/repo --output comment
 */

import { parseArgs } from "node:util";
import { readFileSync } from "node:fs";
import { reviewPR } from "./reviewer.js";

const { values, positionals } = parseArgs({
  options: {
    pr:      { type: "string", short: "p" },
    repo:    { type: "string", short: "r" },
    diff:    { type: "string", short: "d" },
    output:  { type: "string", short: "o", default: "stdout" }, // stdout | comment
    token:   { type: "string", short: "t" },
    model:   { type: "string", short: "m", default: "claude-sonnet-4-20250514" },
    "github-token": { type: "string" },
    help:    { type: "boolean", short: "h", default: false },
  },
  allowPositionals: true,
});

if (values.help) {
  console.log(`
pr-review-agent — Claude-powered PR review

Usage:
  claude-review --pr <url or number> --repo <owner/repo>
  claude-review --diff <file>
  claude-review --pr 123 --repo owner/repo --token ghp_xxx

Environment variables:
  GITHUB_TOKEN       GitHub personal access token (required for --pr mode)
  CLAUDE_API_KEY     Anthropic API key (required)

Options:
  --pr <url|number>  PR URL or PR number
  --repo <owner/repo> Owner/repo slug (required with --pr number)
  --diff <file>      Path to a .diff file (alternative to --pr)
  --output <mode>    Output mode: stdout (default) | comment
  --token <token>    Override GITHUB_TOKEN env var
  --model <model>    Claude model (default: claude-sonnet-4-20250514)
  --help             Show this help
`);
  process.exit(0);
}

const GITHUB_TOKEN = values["github-token"] || values.token || process.env.GITHUB_TOKEN;
const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY;

if (!CLAUDE_API_KEY) {
  console.error("Error: CLAUDE_API_KEY environment variable is required.");
  process.exit(1);
}

async function main() {
  let diffContent: string;

  if (values.diff) {
    diffContent = readFileSync(values.diff, "utf-8");
  } else if (values.pr) {
    if (!values.repo) {
      console.error("Error: --repo <owner/repo> is required with --pr");
      process.exit(1);
    }
    if (!GITHUB_TOKEN) {
      console.error("Error: GITHUB_TOKEN environment variable or --token is required with --pr.");
      process.exit(1);
    }
    const prNumber = extractPRNumber(values.pr);
    diffContent = await fetchPRDiff(values.repo, prNumber, GITHUB_TOKEN);
  } else {
    console.error("Error: provide either --pr or --diff");
    process.exit(1);
  }

  if (!diffContent || diffContent.trim().length === 0) {
    console.error("Error: could not fetch diff content.");
    process.exit(1);
  }

  const review = await reviewPR(diffContent, {
    apiKey: CLAUDE_API_KEY,
    model: values.model || "claude-sonnet-4-20250514",
  });

  console.log(review);

  // Optionally post as GitHub PR comment
  if (values.output === "comment" && values.pr && values.repo && GITHUB_TOKEN) {
    const prNumber = extractPRNumber(values.pr);
    await postPRComment(values.repo, prNumber, review, GITHUB_TOKEN);
  }
}

function extractPRNumber(pr: string): number {
  if (/^\d+$/.test(pr)) return parseInt(pr, 10);
  const match = pr.match(/\/pull\/(\d+)/);
  if (match) return parseInt(match[1], 10);
  throw new Error(`Could not extract PR number from: ${pr}`);
}

async function fetchPRDiff(repo: string, prNumber: number, token: string): Promise<string> {
  const { request } = await import("@octokit/action");
  const github = request.defaults({
    auth: token,
    baseUrl: "https://api.github.com",
  });
  const response = await github.rest.pulls.get({
    owner: repo.split("/")[0],
    repo: repo.split("/")[1],
    pull_number: prNumber,
    mediaType: { format: "diff" },
  });
  return response.data as unknown as string;
}

async function postPRComment(repo: string, prNumber: number, body: string, token: string): Promise<void> {
  const { request } = await import("@octokit/action");
  const github = request.defaults({
    auth: token,
    baseUrl: "https://api.github.com",
  });
  await github.rest.issues.createComment({
    owner: repo.split("/")[0],
    repo: repo.split("/")[1],
    issue_number: prNumber,
    body,
  });
  console.error("Comment posted successfully.");
}

main().catch((err) => {
  console.error("Fatal error:", err.message);
  process.exit(1);
});
