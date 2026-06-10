#!/usr/bin/env node

import { writeFile } from "node:fs/promises";

const usage = `Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr owner/repo#123 --out review.md

Options:
  --pr       GitHub pull request URL or owner/repo#number
  --out      Optional file path for Markdown output
  --help     Show this help text

Environment:
  GITHUB_TOKEN is optional, but recommended for higher API limits.`;

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") args.help = true;
    else if (arg === "--pr") args.pr = argv[++i];
    else if (arg === "--out") args.out = argv[++i];
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return args;
}

function parsePullRequest(input) {
  const shorthand = input.match(/^([^/\s]+)\/([^#\s]+)#(\d+)$/);
  if (shorthand) {
    return {
      owner: shorthand[1],
      repo: shorthand[2],
      number: Number(shorthand[3]),
    };
  }

  const url = new URL(input);
  const match = url.pathname.match(/^\/([^/]+)\/([^/]+)\/pull\/(\d+)\/?$/);
  if (!match) throw new Error("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123");

  return {
    owner: match[1],
    repo: match[2],
    number: Number(match[3]),
  };
}

async function github(path, options = {}) {
  const token = process.env.GITHUB_TOKEN;
  const headers = {
    "Accept": options.accept ?? "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`https://api.github.com${path}`, { headers });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`GitHub API error ${response.status}: ${body.slice(0, 500)}`);
  }
  return options.text ? response.text() : response.json();
}

function summarizeFiles(files) {
  const groups = new Map();
  for (const file of files) {
    const top = file.filename.includes("/") ? file.filename.split("/")[0] : "(root)";
    const current = groups.get(top) ?? { files: 0, additions: 0, deletions: 0 };
    current.files += 1;
    current.additions += file.additions;
    current.deletions += file.deletions;
    groups.set(top, current);
  }

  return [...groups.entries()]
    .sort((a, b) => b[1].files - a[1].files)
    .slice(0, 8)
    .map(([name, data]) => `- ${name}: ${data.files} file(s), +${data.additions}/-${data.deletions}`)
    .join("\n");
}

function detectRisks(pr, files, patchText) {
  const risks = [];
  const changed = files.map((file) => file.filename);
  const lowerPatch = patchText.toLowerCase();

  if (files.length > 20 || pr.additions + pr.deletions > 1200) {
    risks.push("Large change set; review should be split by subsystem or backed by stronger test evidence.");
  }
  if (changed.some((name) => /package-lock|yarn\.lock|pnpm-lock|bun\.lock/.test(name))) {
    risks.push("Dependency lockfile changed; confirm the package updates are intentional and supply-chain risk was reviewed.");
  }
  if (changed.some((name) => /auth|login|session|token|secret|payment|billing|wallet|crypto/i.test(name))) {
    risks.push("Security- or payment-sensitive files changed; verify authorization, input validation, logging, and secret handling.");
  }
  if (lowerPatch.includes("innerhtml") || lowerPatch.includes("dangerouslysetinnerhtml")) {
    risks.push("HTML injection surface appears in the diff; verify content is sanitized before rendering.");
  }
  if (lowerPatch.includes("todo") || lowerPatch.includes("fixme")) {
    risks.push("Diff contains TODO/FIXME markers; confirm they are acceptable before merge.");
  }
  if (!changed.some((name) => /test|spec|__tests__|fixtures/i.test(name))) {
    risks.push("No obvious test files changed; check whether existing tests cover the new behavior.");
  }

  return risks.length ? risks : ["No major automated risk flags found from filenames and patch text."];
}

function suggestions(pr, files) {
  const items = [];
  if (!pr.body || pr.body.trim().length < 120) {
    items.push("Expand the PR description with motivation, scope, and validation steps.");
  }
  if (!files.some((file) => /readme|docs|\.md$/i.test(file.filename))) {
    items.push("Add or update documentation if this changes user-facing behavior or setup steps.");
  }
  if (!files.some((file) => /test|spec|__tests__|fixtures/i.test(file.filename))) {
    items.push("Add focused regression tests or include manual verification evidence in the PR body.");
  }
  items.push("Ask reviewers to focus on the highest-risk changed areas listed above.");
  return items;
}

function confidence(pr, files) {
  let score = 0;
  if (pr.body && pr.body.length > 300) score += 1;
  if (files.some((file) => /test|spec|__tests__|fixtures/i.test(file.filename))) score += 1;
  if (files.length <= 10 && pr.additions + pr.deletions <= 500) score += 1;
  if (score >= 3) return "High";
  if (score === 2) return "Medium";
  return "Low";
}

function renderReview({ pr, files, risks, improvements, confidenceLevel }) {
  const fileSummary = summarizeFiles(files);
  return `# PR Review: ${pr.title}

## Summary
This PR changes ${files.length} file(s) with +${pr.additions}/-${pr.deletions} lines. The main touched areas are:

${fileSummary}

Based on the PR metadata and diff, the change appears focused on: ${pr.title}.

## Identified Risks
${risks.map((risk) => `- ${risk}`).join("\n")}

## Improvement Suggestions
${improvements.map((item) => `- ${item}`).join("\n")}

## Confidence Score
${confidenceLevel}

## Review Metadata
- PR: ${pr.html_url}
- Base: ${pr.base.ref}
- Head: ${pr.head.ref}
- Head SHA: ${pr.head.sha}
`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage);
    return;
  }
  if (!args.pr) throw new Error("--pr is required");

  const { owner, repo, number } = parsePullRequest(args.pr);
  const pr = await github(`/repos/${owner}/${repo}/pulls/${number}`);
  const files = await github(`/repos/${owner}/${repo}/pulls/${number}/files?per_page=100`);
  const patchText = await github(`/repos/${owner}/${repo}/pulls/${number}`, {
    accept: "application/vnd.github.v3.diff",
    text: true,
  });

  const output = renderReview({
    pr,
    files,
    risks: detectRisks(pr, files, patchText),
    improvements: suggestions(pr, files),
    confidenceLevel: confidence(pr, files),
  });

  if (args.out) {
    await writeFile(args.out, output);
  } else {
    process.stdout.write(output);
  }
}

main().catch((error) => {
  console.error(`claude-review: ${error.message}`);
  process.exit(1);
});
