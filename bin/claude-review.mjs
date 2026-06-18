#!/usr/bin/env node

import { writeFile } from "node:fs/promises";

const DEFAULT_MODEL = process.env.CLAUDE_MODEL || "claude-sonnet-4-20250514";

function usage() {
  return `Usage:
  claude-review --pr https://github.com/owner/repo/pull/123 [options]

Options:
  --pr <url>          GitHub pull request URL to review (required)
  --output <file>     Write the Markdown review to a file
  --model <name>      Claude model name (default: ${DEFAULT_MODEL})
  --no-ai             Skip Anthropic API even if ANTHROPIC_API_KEY is set
  --help              Show this help

Environment:
  ANTHROPIC_API_KEY   Optional. When set, Claude generates the final review.
  GITHUB_TOKEN        Optional. Used for higher GitHub API rate limits.
`;
}

function parseArgs(argv) {
  const args = { model: DEFAULT_MODEL, useAi: true };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") args.help = true;
    else if (arg === "--no-ai") args.useAi = false;
    else if (arg === "--pr") args.pr = argv[++i];
    else if (arg === "--output" || arg === "-o") args.output = argv[++i];
    else if (arg === "--model") args.model = argv[++i];
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return args;
}

function parsePullRequestUrl(url) {
  const match = String(url || "").match(/^https:\/\/github\.com\/([^/\s]+)\/([^/\s]+)\/pull\/(\d+)(?:[/?#].*)?$/);
  if (!match) {
    throw new Error("Expected --pr to be a GitHub pull request URL like https://github.com/owner/repo/pull/123");
  }
  return { owner: match[1], repo: match[2], number: Number(match[3]), url };
}

async function githubFetch(url, accept = "application/vnd.github+json") {
  const headers = {
    Accept: accept,
    "User-Agent": "claude-review-bounty-cli"
  };
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  const response = await fetch(url, { headers });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`GitHub request failed ${response.status} ${response.statusText}: ${body.slice(0, 300)}`);
  }
  return accept.includes("diff") ? response.text() : response.json();
}

async function loadPullRequest({ owner, repo, number }) {
  const apiBase = `https://api.github.com/repos/${owner}/${repo}/pulls/${number}`;
  const [pr, files, diff] = await Promise.all([
    githubFetch(apiBase),
    githubFetch(`${apiBase}/files?per_page=100`),
    githubFetch(apiBase, "application/vnd.github.v3.diff")
  ]);
  return { pr, files, diff };
}

function summarizeFiles(files) {
  const totalAdditions = files.reduce((sum, file) => sum + file.additions, 0);
  const totalDeletions = files.reduce((sum, file) => sum + file.deletions, 0);
  const changed = files.map((file) => `${file.status}: ${file.filename} (+${file.additions}/-${file.deletions})`);
  return { totalAdditions, totalDeletions, changed };
}

function riskSignals(files, diff) {
  const risks = [];
  const filenames = files.map((file) => file.filename);
  const lowerDiff = diff.toLowerCase();

  if (files.length > 20) risks.push("Large surface area: more than 20 files changed, so integration risk is higher.");
  if (files.some((file) => file.changes > 500)) risks.push("At least one file has more than 500 changed lines and deserves focused manual review.");
  if (filenames.some((name) => /^\.github\/workflows\//.test(name))) risks.push("CI/CD workflow files changed; verify permissions, triggers, and secret exposure.");
  if (filenames.some((name) => /(^|\/)(package-lock|pnpm-lock|yarn\.lock|poetry\.lock|requirements\.txt|package\.json)$/.test(name))) {
    risks.push("Dependency or package metadata changed; check lockfile integrity and supply-chain impact.");
  }
  if (filenames.some((name) => /migration|schema|database|db\//i.test(name))) risks.push("Database or schema-related files changed; confirm migration ordering and rollback behavior.");
  if (!filenames.some((name) => /(^|\/)(test|tests|spec|__tests__)\//i.test(name) || /\.(test|spec)\.[cm]?[jt]sx?$/i.test(name))) {
    risks.push("No obvious test files changed; request or run coverage for the modified behavior.");
  }
  if (/\b(todo|fixme|hack)\b/.test(lowerDiff)) risks.push("Diff contains TODO/FIXME/HACK markers that may indicate unfinished work.");
  if (/(api[_-]?key|secret|password|token)\s*[:=]/i.test(diff)) risks.push("Potential secret-like strings appear in the diff; verify no credentials are committed.");
  if (files.some((file) => file.status === "removed")) risks.push("Files were removed; confirm no runtime references or documentation links still depend on them.");

  return risks.length ? risks : ["No major structural risk signals were detected from filenames and diff metadata."];
}

function suggestions(files, risks) {
  const notes = [
    "Run the repository's normal test and lint commands before merge.",
    "Ask the author to document any non-obvious behavior or operational steps introduced by the PR."
  ];

  if (risks.some((risk) => risk.includes("No obvious test"))) {
    notes.unshift("Add or identify tests that cover the changed behavior, especially edge cases touched by the diff.");
  }
  if (files.some((file) => /^\.github\/workflows\//.test(file.filename))) {
    notes.push("Review GitHub Action permission scopes and confirm the workflow cannot run untrusted code with privileged secrets.");
  }
  if (files.some((file) => /package\.json|requirements\.txt|lock$/i.test(file.filename))) {
    notes.push("Run dependency audit tooling appropriate for the ecosystem.");
  }
  return notes;
}

function confidenceFor(files, risks) {
  if (files.length > 25 || risks.length >= 5) return "Low";
  if (files.length > 8 || risks.length >= 3) return "Medium";
  return "High";
}

function heuristicReview(prInfo, files, diff) {
  const { totalAdditions, totalDeletions, changed } = summarizeFiles(files);
  const risks = riskSignals(files, diff);
  const recs = suggestions(files, risks);
  const confidence = confidenceFor(files, risks);
  const title = prInfo.pr.title || `PR #${prInfo.pr.number}`;
  const repo = prInfo.pr.base?.repo?.full_name || "the repository";

  return `## Summary of changes
This PR, **${title}**, targets \`${repo}\` and changes ${files.length} file(s) with +${totalAdditions}/-${totalDeletions} lines. The main touched files are:
${changed.slice(0, 10).map((line) => `- ${line}`).join("\n")}${changed.length > 10 ? `\n- ...and ${changed.length - 10} more file(s)` : ""}

## Identified risks
${risks.map((risk) => `- ${risk}`).join("\n")}

## Improvement suggestions
${recs.map((suggestion) => `- ${suggestion}`).join("\n")}

## Confidence score: ${confidence}
Confidence is based on diff size, file types, test visibility, and automated risk signals.`;
}

function buildPrompt(prInfo, files, diff) {
  const { totalAdditions, totalDeletions, changed } = summarizeFiles(files);
  return `You are a Claude Code PR review sub-agent. Review the GitHub pull request below and return only structured Markdown with exactly these sections:

## Summary of changes
2-3 sentences.

## Identified risks
Bullet list.

## Improvement suggestions
Bullet list.

## Confidence score: Low|Medium|High
One short explanation.

PR: ${prInfo.pr.html_url}
Title: ${prInfo.pr.title}
Author: ${prInfo.pr.user?.login}
Base: ${prInfo.pr.base?.ref}
Head: ${prInfo.pr.head?.ref}
Files changed: ${files.length}
Lines: +${totalAdditions}/-${totalDeletions}

Changed files:
${changed.join("\n")}

Diff:
${diff.slice(0, 60000)}
`;
}

async function claudeReview(prompt, model) {
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": process.env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01"
    },
    body: JSON.stringify({
      model,
      max_tokens: 1200,
      messages: [{ role: "user", content: prompt }]
    })
  });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`Claude request failed ${response.status} ${response.statusText}: ${body.slice(0, 300)}`);
  }
  const data = await response.json();
  return data.content?.map((part) => part.text || "").join("\n").trim();
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }
  if (!args.pr) throw new Error("--pr is required\n\n" + usage());

  const prRef = parsePullRequestUrl(args.pr);
  const prInfo = await loadPullRequest(prRef);

  let markdown;
  if (args.useAi && process.env.ANTHROPIC_API_KEY) {
    try {
      markdown = await claudeReview(buildPrompt(prInfo, prInfo.files, prInfo.diff), args.model);
    } catch (error) {
      markdown = `${heuristicReview(prInfo, prInfo.files, prInfo.diff)}\n\n> Note: Claude API generation failed, so this review was produced by the deterministic fallback analyzer. Error: ${error.message}`;
    }
  } else {
    markdown = heuristicReview(prInfo, prInfo.files, prInfo.diff);
  }

  if (args.output) await writeFile(args.output, `${markdown}\n`, "utf8");
  console.log(markdown);
}

main().catch((error) => {
  console.error(`claude-review failed: ${error.message}`);
  process.exit(1);
});
