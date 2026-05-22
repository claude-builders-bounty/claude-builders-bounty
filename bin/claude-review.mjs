#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const USER_AGENT = "claude-pr-review-agent";

function usage() {
  return [
    "Usage:",
    "  claude-review --pr https://github.com/owner/repo/pull/123 [--post] [--output review.md]",
    "",
    "Options:",
    "  --pr URL          GitHub pull request URL to review.",
    "  --post           Post the Markdown review as a PR comment. Requires GITHUB_TOKEN.",
    "  --output FILE    Write the Markdown review to a file.",
    "  --max-files N    Maximum changed files to include in the prompt. Default: 20.",
    "  --no-claude      Skip Claude CLI even when it is installed.",
    "  --help           Show this help.",
    ""
  ].join("\n");
}

function parseArgs(argv) {
  const args = { maxFiles: 20, post: false, noClaude: false };
  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--help" || arg === "-h") args.help = true;
    else if (arg === "--post") args.post = true;
    else if (arg === "--no-claude") args.noClaude = true;
    else if (arg === "--pr") args.pr = argv[++index];
    else if (arg === "--output") args.output = argv[++index];
    else if (arg === "--max-files") args.maxFiles = Number(argv[++index]);
    else throw new Error("Unknown argument: " + arg);
  }
  return args;
}

function parsePrUrl(value) {
  const match = String(value || "").match(/^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)(?:\b|$)/);
  if (!match) throw new Error("--pr must be a GitHub pull request URL.");
  return { owner: match[1], repo: match[2], number: Number(match[3]) };
}

async function githubJson(path, token) {
  const signal = AbortSignal.timeout(Number(process.env.CLAUDE_REVIEW_TIMEOUT_MS || 20000));
  const response = await fetch("https://api.github.com" + path, {
    signal,
    headers: {
      Accept: "application/vnd.github+json",
      "User-Agent": USER_AGENT,
      ...(token ? { Authorization: "Bearer " + token } : {})
    }
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error("GitHub API " + response.status + " for " + path + ": " + body.slice(0, 300));
  }
  return response.json();
}

async function loadPullRequest(prUrl, maxFiles) {
  const parsed = parsePrUrl(prUrl);
  const token = process.env.GITHUB_TOKEN || "";
  const pull = await githubJson("/repos/" + parsed.owner + "/" + parsed.repo + "/pulls/" + parsed.number, token);
  const perPage = Math.max(1, Math.min(maxFiles, 100));
  const files = await githubJson("/repos/" + parsed.owner + "/" + parsed.repo + "/pulls/" + parsed.number + "/files?per_page=" + perPage, token);
  return { owner: parsed.owner, repo: parsed.repo, number: parsed.number, pull, files };
}

function summarizeFiles(files) {
  return files.map((file) => {
    const patch = file.patch ? file.patch.slice(0, 12000) : "[binary or large file without patch]";
    return [
      "File: " + file.filename,
      "Status: " + file.status + "; additions: " + file.additions + "; deletions: " + file.deletions,
      "Patch:",
      patch
    ].join("\n");
  }).join("\n\n---\n\n");
}

function buildPrompt(context) {
  const pull = context.pull;
  const author = pull.user && pull.user.login ? pull.user.login : "unknown";
  const base = pull.base && pull.base.ref ? pull.base.ref : "unknown";
  const head = pull.head && pull.head.ref ? pull.head.ref : "unknown";
  return [
    "You are a senior code reviewer. Review this GitHub pull request and return only a structured Markdown review comment.",
    "",
    "Repository: " + context.owner + "/" + context.repo,
    "Pull request: #" + context.number + " - " + pull.title,
    "Author: " + author,
    "Base: " + base,
    "Head: " + head,
    "Changed files loaded: " + context.files.length,
    "PR body:",
    pull.body || "(empty)",
    "",
    "Required output shape:",
    "## Summary",
    "2-3 sentences.",
    "",
    "## Identified Risks",
    "- Bullet list. Use \"None found from the loaded diff.\" if there are no concrete risks.",
    "",
    "## Improvement Suggestions",
    "- Bullet list. Keep suggestions actionable.",
    "",
    "## Confidence",
    "Low, Medium, or High, with one short reason.",
    "",
    "Diff excerpts:",
    summarizeFiles(context.files)
  ].join("\n");
}

function runClaude(prompt) {
  const command = process.env.CLAUDE_REVIEW_COMMAND || "claude";
  const result = spawnSync(command, ["-p", prompt], {
    encoding: "utf8",
    maxBuffer: 1024 * 1024 * 8,
    shell: process.platform === "win32"
  });
  if (result.error || result.status !== 0 || !result.stdout.trim()) return null;
  return result.stdout.trim();
}

function riskForFile(file) {
  const patch = file.patch || "";
  const risks = [];
  if (/process\.env|secret|token|password|api[_-]?key/i.test(patch)) {
    risks.push("- " + file.filename + ": touches credential or environment-sensitive code; verify secrets are not logged or committed.");
  }
  if (/(?:\bauth(?:entication|orization)?\b|\blogin\b|\bsession\b|\bpermission\b|\brole\b|\badmin\b)/i.test(file.filename)) {
    risks.push("- " + file.filename + ": changes authorization-adjacent behavior; verify access boundaries and negative cases.");
  }
  if (/delete|remove|drop|truncate|migration/i.test(patch)) {
    risks.push("- " + file.filename + ": includes destructive or migration-like changes; confirm rollback and data-safety behavior.");
  }
  if (/TODO|FIXME|throw new Error\(|console\.log/i.test(patch)) {
    risks.push("- " + file.filename + ": leaves debugging, placeholder, or intentionally failing code in the diff.");
  }
  return risks;
}

function fallbackReview(context) {
  const additions = context.files.reduce((sum, file) => sum + file.additions, 0);
  const deletions = context.files.reduce((sum, file) => sum + file.deletions, 0);
  const filenames = context.files.map((file) => file.filename);
  const risks = context.files.flatMap(riskForFile);
  const allTextLoaded = context.files.length > 0 && context.files.every((file) => file.patch || file.changes === 0);
  const confidence = allTextLoaded ? "Medium" : "Low";
  const pathList = filenames.slice(0, 5).join(", ") + (filenames.length > 5 ? ", and others" : "");
  return [
    "## Summary",
    "This PR updates " + context.files.length + " file(s) in " + context.owner + "/" + context.repo + ", with " + additions + " additions and " + deletions + " deletions across the loaded diff. The main touched paths are " + pathList + ". Based on the available patch excerpts for PR #" + context.number + ", the change appears scoped to: " + context.pull.title + ".",
    "",
    "## Identified Risks",
    risks.length ? risks.join("\n") : "- None found from the loaded diff.",
    "",
    "## Improvement Suggestions",
    "- Run the repository's relevant tests or type checks before merge and include the command output in the PR.",
    "- Add or update focused tests for the changed behavior if the diff affects runtime logic.",
    "- Keep the PR description aligned with the final implementation, especially any setup, migration, or release notes.",
    "",
    "## Confidence",
    confidence + " - this review is based on GitHub metadata and the loaded diff excerpts" + (confidence === "Low" ? ", and at least one file did not expose a full textual patch." : ".")
  ].join("\n");
}

async function postComment(context, body) {
  const token = process.env.GITHUB_TOKEN;
  if (!token) throw new Error("--post requires GITHUB_TOKEN with pull request comment permissions.");
  const response = await fetch("https://api.github.com/repos/" + context.owner + "/" + context.repo + "/issues/" + context.number + "/comments", {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
      "User-Agent": USER_AGENT,
      Authorization: "Bearer " + token
    },
    body: JSON.stringify({ body })
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error("Failed to post comment: " + response.status + " " + detail.slice(0, 300));
  }
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    process.stdout.write(usage());
    return;
  }
  if (!args.pr) throw new Error("--pr is required.");

  const context = await loadPullRequest(args.pr, args.maxFiles);
  const prompt = buildPrompt(context);
  const review = args.noClaude ? fallbackReview(context) : (runClaude(prompt) || fallbackReview(context));

  if (args.output) writeFileSync(args.output, review + "\n", "utf8");
  if (args.post) await postComment(context, review);
  process.stdout.write(review + "\n");
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
