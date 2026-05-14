#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(__dirname, "..");

function usage() {
  console.log(`Usage:
  claude-review --pr https://github.com/owner/repo/pull/123 [options]

Options:
  --pr URL                      GitHub pull request URL.
  --engine auto|claude|local    Review engine. Default: auto.
  --max-diff-chars N            Maximum diff chars sent to Claude mode. Default: 60000.
  --max-budget-usd N            Maximum Claude Code spend in Claude mode. Default: 0.25.
  -h, --help                    Show this help text.`);
}

function parseArgs(argv) {
  const args = {
    engine: "auto",
    maxDiffChars: 60000,
    maxBudgetUsd: 0.25
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--pr") {
      args.pr = argv[++index];
    } else if (arg === "--engine") {
      args.engine = argv[++index];
    } else if (arg === "--max-diff-chars") {
      args.maxDiffChars = Number(argv[++index]);
    } else if (arg === "--max-budget-usd") {
      args.maxBudgetUsd = Number(argv[++index]);
    } else if (arg === "-h" || arg === "--help") {
      args.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (args.help) return args;
  if (!args.pr) throw new Error("Missing required --pr URL.");
  if (!["auto", "local", "claude"].includes(args.engine)) {
    throw new Error("--engine must be auto, local, or claude.");
  }
  if (!Number.isFinite(args.maxDiffChars) || args.maxDiffChars < 1000) {
    throw new Error("--max-diff-chars must be a number of at least 1000.");
  }
  if (!Number.isFinite(args.maxBudgetUsd) || args.maxBudgetUsd <= 0) {
    throw new Error("--max-budget-usd must be a positive number.");
  }

  return args;
}

function parsePullRequestUrl(value) {
  const url = new URL(value);
  if (url.hostname !== "github.com") {
    throw new Error("Only github.com pull request URLs are supported.");
  }

  const parts = url.pathname.split("/").filter(Boolean);
  if (parts.length < 4 || parts[2] !== "pull") {
    throw new Error("Expected URL format: https://github.com/owner/repo/pull/123");
  }

  const number = Number(parts[3]);
  if (!Number.isInteger(number) || number < 1) {
    throw new Error("Pull request number must be a positive integer.");
  }

  return {
    owner: parts[0],
    repo: parts[1],
    number,
    url: `https://github.com/${parts[0]}/${parts[1]}/pull/${number}`
  };
}

function githubHeaders(accept) {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  const headers = {
    accept,
    "user-agent": "claude-pr-reviewer-agent"
  };

  if (token) headers.authorization = `Bearer ${token}`;
  return headers;
}

async function fetchGithubJson(pathname) {
  const response = await fetch(`https://api.github.com${pathname}`, {
    headers: githubHeaders("application/vnd.github+json")
  });

  if (!response.ok) {
    throw new Error(`GitHub ${response.status}: ${await response.text()}`);
  }

  return response.json();
}

async function fetchGithubDiff(pathname) {
  const response = await fetch(`https://api.github.com${pathname}`, {
    headers: githubHeaders("application/vnd.github.v3.diff")
  });

  if (!response.ok) {
    throw new Error(`GitHub ${response.status}: ${await response.text()}`);
  }

  return response.text();
}

function parseDiff(diff) {
  const files = [];
  let current = null;

  for (const line of diff.split("\n")) {
    if (line.startsWith("diff --git ")) {
      const match = line.match(/^diff --git a\/(.+) b\/(.+)$/);
      current = {
        path: match?.[2] || "unknown",
        additions: 0,
        deletions: 0,
        hunks: 0
      };
      files.push(current);
      continue;
    }

    if (!current) continue;
    if (line.startsWith("@@")) current.hunks += 1;
    if (line.startsWith("+") && !line.startsWith("+++")) current.additions += 1;
    if (line.startsWith("-") && !line.startsWith("---")) current.deletions += 1;
  }

  return files;
}

function fileKind(pathname) {
  if (/(\btest\b|\bspec\b|__tests__|\.test\.|\.spec\.)/i.test(pathname)) return "tests";
  if (/\.md$|docs?\//i.test(pathname)) return "docs";
  if (/package(-lock)?\.json$|pnpm-lock\.yaml$|yarn\.lock$/i.test(pathname)) return "dependencies";
  if (/\.github\/workflows\//i.test(pathname)) return "workflow";
  if (/migration|schema|\.sql$/i.test(pathname)) return "database";
  if (/\.(js|jsx|ts|tsx|mjs|cjs|py|rb|go|rs|java|cs|sh|bash|zsh)$/i.test(pathname)) return "source";
  return "other";
}

function summarizeKinds(files) {
  const counts = new Map();
  for (const file of files) {
    const kind = fileKind(file.path);
    counts.set(kind, (counts.get(kind) || 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

function formatKindList(kindCounts) {
  if (kindCounts.length === 0) return "no files";
  return kindCounts.map(([kind, count]) => `${count} ${kind}`).join(", ");
}

function hasKind(files, kind) {
  return files.some((file) => fileKind(file.path) === kind);
}

function localReview(pr, diff) {
  const files = parseDiff(diff);
  const additions = files.reduce((sum, file) => sum + file.additions, 0);
  const deletions = files.reduce((sum, file) => sum + file.deletions, 0);
  const kindCounts = summarizeKinds(files);
  const totalTouched = additions + deletions;

  const summary = [
    `PR #${pr.number} in ${pr.base.repo.full_name} changes ${files.length} file${files.length === 1 ? "" : "s"} with ${additions} additions and ${deletions} deletions.`,
    `The diff is concentrated around ${formatKindList(kindCounts)}, based on the files visible in the GitHub PR diff.`,
    "This is a first-pass review generated from the diff only, so maintainer intent and runtime behavior should still be checked during normal review."
  ];

  const risks = [];
  const suggestions = [];

  if (hasKind(files, "source") && !hasKind(files, "tests")) {
    risks.push("No obvious test files changed alongside source changes, so regressions may be missed.");
    suggestions.push("Add or update focused tests for the changed behavior, or note why existing coverage is sufficient.");
  }
  if (hasKind(files, "dependencies")) {
    risks.push("Dependency or lockfile changes can alter runtime behavior beyond the visible source diff.");
    suggestions.push("Confirm dependency updates are intentional and run the project install/test path from a clean checkout.");
  }
  if (hasKind(files, "workflow")) {
    risks.push("Workflow changes can affect CI, release, or automation behavior for future contributors.");
    suggestions.push("Document any new secrets, permissions, or runner assumptions required by the workflow.");
  }
  if (hasKind(files, "database")) {
    risks.push("Database or migration changes can affect existing data and rollback safety.");
    suggestions.push("Include migration, rollback, and data validation notes in the PR description.");
  }
  if (deletions > additions * 2 && deletions > 50) {
    risks.push("The diff removes substantially more code than it adds, which raises compatibility and missing-behavior risk.");
    suggestions.push("Call out removed behavior explicitly so reviewers can confirm it is intentional.");
  }
  if (files.length > 20 || totalTouched > 1000) {
    risks.push("The diff is large enough that important details may be hard to review manually.");
    suggestions.push("Split unrelated changes or add a guided review checklist in the PR description.");
  }
  if (risks.length === 0) {
    risks.push("No major structural risks are visible from the diff alone.");
  }
  if (!hasKind(files, "docs") && (hasKind(files, "source") || hasKind(files, "workflow"))) {
    suggestions.push("Add a short usage or reviewer note if the change affects setup, behavior, or maintenance workflow.");
  }
  if (suggestions.length === 0) {
    suggestions.push("Keep the PR description aligned with the changed files so reviewers can verify intent quickly.");
  }

  let confidence = "High";
  if (files.length > 12 || totalTouched > 500) confidence = "Medium";
  if (files.length > 30 || totalTouched > 1500 || diff.length > 200000) confidence = "Low";
  if (hasKind(files, "source") && !hasKind(files, "tests")) confidence = confidence === "High" ? "Medium" : confidence;

  return renderReview(summary, risks, suggestions, confidence);
}

function renderReview(summary, risks, suggestions, confidence) {
  return `## Summary of Changes

${summary.join(" ")}

## Identified Risks

${risks.map((risk) => `- ${risk}`).join("\n")}

## Improvement Suggestions

${suggestions.map((suggestion) => `- ${suggestion}`).join("\n")}

## Confidence Score

${confidence}
`;
}

function buildClaudePrompt(pr, diff, maxDiffChars) {
  const clipped = diff.length > maxDiffChars
    ? `${diff.slice(0, maxDiffChars)}\n\n[Diff clipped at ${maxDiffChars} characters]`
    : diff;

  return `Review this GitHub pull request and return only the required structured Markdown comment.

PR: ${pr.html_url}
Title: ${pr.title}
Author: ${pr.user?.login || "unknown"}
Base: ${pr.base?.ref || "unknown"}
Head: ${pr.head?.ref || "unknown"}

Diff:
\`\`\`diff
${clipped}
\`\`\`
`;
}

function runClaudeReview(pr, diff, maxDiffChars, maxBudgetUsd) {
  const prompt = buildClaudePrompt(pr, diff, maxDiffChars);
  const npxArgs = [
    "-y",
    "@anthropic-ai/claude-code",
    "--print",
    "--agent",
    "pr-reviewer",
    "--permission-mode",
    "dontAsk",
    "--max-budget-usd",
    String(maxBudgetUsd),
    "--output-format",
    "text"
  ];
  const claudeArgs = [
    "--print",
    "--agent",
    "pr-reviewer",
    "--permission-mode",
    "dontAsk",
    "--max-budget-usd",
    String(maxBudgetUsd),
    "--output-format",
    "text"
  ];
  const commands = [
    process.platform === "win32"
      ? { command: "cmd.exe", args: ["/c", "npx", ...npxArgs] }
      : { command: "npx", args: npxArgs },
    process.platform === "win32"
      ? { command: "cmd.exe", args: ["/c", "claude", ...claudeArgs] }
      : { command: "claude", args: claudeArgs }
  ];

  const errors = [];
  for (const candidate of commands) {
    const result = spawnSync(candidate.command, candidate.args, {
      cwd: packageRoot,
      input: prompt,
      encoding: "utf8",
      maxBuffer: 1024 * 1024 * 8
    });

    if (result.status === 0 && result.stdout.trim()) {
      return result.stdout.trim() + "\n";
    }
    const detail = result.error?.message || result.stderr?.trim() || `exit ${result.status}`;
    errors.push(`${candidate.command}: ${detail}`);
  }

  throw new Error(`Claude engine failed. Run with --engine local for deterministic review output. ${errors.join(" | ")}`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    return;
  }

  const parsed = parsePullRequestUrl(args.pr);
  const apiPath = `/repos/${encodeURIComponent(parsed.owner)}/${encodeURIComponent(parsed.repo)}/pulls/${parsed.number}`;
  const pr = await fetchGithubJson(apiPath);
  const diff = await fetchGithubDiff(apiPath);
  let review;
  if (args.engine === "claude") {
    review = runClaudeReview(pr, diff, args.maxDiffChars, args.maxBudgetUsd);
  } else if (args.engine === "auto") {
    try {
      review = runClaudeReview(pr, diff, args.maxDiffChars, args.maxBudgetUsd);
    } catch (error) {
      console.error(`claude-review: ${error.message}`);
      console.error("claude-review: falling back to local deterministic review.");
      review = localReview(pr, diff);
    }
  } else {
    review = localReview(pr, diff);
  }

  process.stdout.write(review);
}

main().catch((error) => {
  console.error(`claude-review: ${error.message}`);
  process.exit(1);
});
