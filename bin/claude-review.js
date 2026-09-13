#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { stdin as input } from "node:process";
import { reviewPullRequestDiff } from "../src/review.js";

function usage() {
  return [
    "Usage:",
    "  claude-review --pr https://github.com/owner/repo/pull/123",
    "  claude-review --diff ./path/to/pr.diff",
    "  cat pr.diff | claude-review --stdin",
    "",
    "Options:",
    "  --pr <url>      GitHub pull request URL to fetch as a .diff",
    "  --diff <path>   Local unified diff file",
    "  --stdin         Read unified diff from stdin",
    "  --help          Show this help text"
  ].join("\n");
}

function getArg(name) {
  const index = process.argv.indexOf(name);
  return index === -1 ? null : process.argv[index + 1] ?? null;
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of input) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

function toDiffUrl(prUrl) {
  const url = new URL(prUrl);
  if (url.hostname !== "github.com") {
    throw new Error("Only github.com pull request URLs are supported.");
  }
  if (!/\/pull\/\d+\/?$/.test(url.pathname)) {
    throw new Error("Expected a GitHub pull request URL like https://github.com/owner/repo/pull/123.");
  }
  url.pathname = url.pathname.replace(/\/?$/, ".diff");
  url.search = "";
  url.hash = "";
  return url.toString();
}

async function fetchDiff(prUrl) {
  const response = await fetch(toDiffUrl(prUrl), {
    headers: {
      "User-Agent": "claude-pr-review-agent",
      Accept: "text/plain"
    }
  });

  if (!response.ok) {
    throw new Error(`GitHub returned ${response.status} while fetching the PR diff.`);
  }

  return response.text();
}

async function main() {
  if (process.argv.includes("--help") || process.argv.length <= 2) {
    console.log(usage());
    return;
  }

  const prUrl = getArg("--pr");
  const diffPath = getArg("--diff");
  const fromStdin = process.argv.includes("--stdin");

  const selectedInputs = [prUrl, diffPath, fromStdin].filter(Boolean).length;
  if (selectedInputs !== 1) {
    throw new Error("Choose exactly one input: --pr, --diff, or --stdin.");
  }

  const diff = prUrl
    ? await fetchDiff(prUrl)
    : diffPath
      ? await readFile(diffPath, "utf8")
      : await readStdin();

  if (!diff.trim()) {
    throw new Error("The diff input is empty.");
  }

  console.log(reviewPullRequestDiff(diff, { source: prUrl ?? diffPath ?? "stdin" }));
}

main().catch((error) => {
  console.error(`claude-review: ${error.message}`);
  process.exitCode = 1;
});
