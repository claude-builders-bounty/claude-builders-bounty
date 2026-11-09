#!/usr/bin/env node
/**
 * pr-review-agent.js - Claude Code sub-agent that reviews PRs and posts structured comments.
 *
 * Usage:
 *   node pr-review-agent.js --pr-url <url> [--post-comment]
 *
 * Environment:
 *   GITHUB_TOKEN       GitHub PAT with `repo` scope (required)
 *   GITHUB_API_URL     GitHub API base (default: https://api.github.com)
 */

import { execSync } from "node:child_process";
import { writeFileSync, readFileSync, existsSync } from "node:fs";

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const API_URL = process.env.GITHUB_API_URL || "https://api.github.com";

if (!GITHUB_TOKEN) {
  console.error("ERROR: GITHUB_TOKEN environment variable is required");
  process.exit(1);
}

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--pr-url" && i + 1 < argv.length) args.prUrl = argv[++i];
    else if (a === "--post-comment") args.postComment = true;
    else if (a === "--help" || a === "-h") {
      console.log("Usage: node pr-review-agent.js --pr-url <url> [--post-comment]");
      process.exit(0);
    }
  }
  return args;
}

const { prUrl, postComment } = parseArgs(process.argv);

if (!prUrl) {
  console.error("ERROR: --pr-url is required");
  process.exit(1);
}

// Parse owner/repo/prNumber from URL
const m = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
if (!m) {
  console.error("ERROR: Invalid PR URL. Expected: https://github.com/owner/repo/pull/123");
  process.exit(1);
}
const [, owner, repo, prNumber] = m;

function apiGet(path) {
  const url = `${API_URL}${path}`;
  const out = execSync(
    `curl -s -H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" "${url}"`,
    { encoding: "utf8" }
  );
  return JSON.parse(out);
}

function apiPost(path, body) {
  const out = execSync(
    `curl -s -X POST -H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" -H "Content-Type: application/json" -d '${JSON.stringify(body)}' "${API_URL}${path}"`,
    { encoding: "utf8" }
  );
  return JSON.parse(out);
}

// Fetch PR metadata
console.log(`Fetching PR #${prNumber} from ${owner}/${repo}...`);
const pr = apiGet(`/repos/${owner}/${repo}/pulls/${prNumber}`);
const prTitle = pr.title || "";
const prBody = pr.body || "";
const prState = pr.state || "open";
const prAdditions = pr.additions || 0;
const prDeletions = pr.deletions || 0;
const prChangedFiles = pr.changed_files || 0;

// Fetch PR files (diff)
let files = [];
try {
  files = apiGet(`/repos/${owner}/${repo}/pulls/${prNumber}/files`);
} catch (e) {
  console.error("WARNING: Could not fetch PR files:", e.message);
}

// Analyze each file
const findings = {
  security: [],
  performance: [],
  quality: [],
  breaking: [],
  documentation: [],
};

for (const file of files) {
  const filename = file.filename || "";
  const patch = file.patch || "";
  const status = file.status || "";
  const additions = file.additions || 0;
  const deletions = file.deletions || 0;

  // Skip deleted files for patch analysis
  if (status === "removed") continue;

  // --- Security checks ---
  if (patch.includes("AKIA") || patch.includes("ghp_") || patch.includes("sk_live_") || patch.includes("xoxb-")) {
    findings.security.push({
      file,
      line: 0,
      severity: "HIGH",
      message: "Possible hardcoded secret or API key detected",
      suggestion: "Move secrets to environment variables or a secrets manager",
    });
  }

  if (patch.includes("eval(") || patch.includes("exec(") || patch.includes("child_process.exec")) {
    findings.security.push({
      file,
      line: 0,
      severity: "HIGH",
      message: "Potential code injection via eval/exec/child_process",
      suggestion: "Validate and sanitize all inputs; avoid eval/exec",
    });
  }

  // --- Performance checks ---
  if (patch.includes(".forEach(") && patch.includes("await ")) {
    findings.performance.push({
      file,
      line: 0,
      severity: "MEDIUM",
      message: "Possible sequential await inside loop — consider Promise.all()",
      suggestion: "Batch independent async operations with Promise.all()",
    });
  }

  if (additions > 500) {
    findings.performance.push({
      file,
      line: 0,
      severity: "LOW",
      message: `Large file change (+${additions} lines) — consider splitting into smaller PRs`,
      suggestion: "Break into smaller, focused pull requests",
    });
  }

  // --- Quality checks ---
  if (filename.endsWith(".ts") || filename.endsWith(".tsx")) {
    if (patch.includes("any")) {
      findings.quality.push({
        file,
        line: 0,
        severity: "LOW",
        message: "Use of `any` type reduces type safety",
        suggestion: "Define explicit TypeScript interfaces or types",
      });
    }
  }

  if (!patch.includes(".test.") && !patch.includes(".spec.") && additions > 50) {
    findings.quality.push({
      file,
      line: 0,
      severity: "LOW",
      message: "No test file added for significant new code",
      suggestion: "Add unit tests for new functionality",
    });
  }

  // --- Breaking changes ---
  if (status === "removed" && (filename.endsWith(".ts") || filename.endsWith(".tsx") || filename.endsWith(".js"))) {
    findings.breaking.push({
      file,
      line: 0,
      severity: "HIGH",
      message: `File removed: ${filename} — may break importers`,
      suggestion: "Add deprecation period or migration guide",
    });
  }

  // --- Documentation ---
  if (additions > 100 && !patch.includes("README") && !patch.includes("CHANGELOG")) {
    findings.documentation.push({
      file,
      line: 0,
      severity: "LOW",
      message: "Large change without README or CHANGELOG update",
      suggestion: "Update documentation to reflect changes",
    });
  }
}

// Build review comment
const totalFindings =
  findings.security.length +
  findings.performance.length +
  findings.quality.length +
  findings.breaking.length +
  findings.documentation.length;

let decision = "APPROVE";
if (findings.security.some((f) => f.severity === "HIGH")) decision = "REQUEST_CHANGES";
else if (findings.breaking.length > 0) decision = "REQUEST_CHANGES";
else if (totalFindings > 5) decision = "REQUEST_CHANGES";
else if (totalFindings > 0) decision = "COMMENT";

const lines = [];
lines.push(`## PR Review: #${prNumber} — ${prTitle}`);
lines.push("");
lines.push(`**Decision:** ${decision}`);
lines.push("");
lines.push("### Summary");
lines.push(
  `Changes across ${prChangedFiles} files (+${prAdditions}/-${prDeletions} lines).`
);
lines.push("");

const sections = [
  { key: "security", title: "Security" },
  { key: "performance", title: "Performance" },
  { key: "quality", title: "Code Quality" },
  { key: "breaking", title: "Breaking Changes" },
  { key: "documentation", title: "Documentation" },
];

for (const { key, title } of sections) {
  const items = findings[key];
  if (items.length === 0) continue;
  lines.push(`### ${title}`);
  for (const item of items) {
    lines.push(
      `- **${item.severity}:** ${item.message} (\`${item.file}\`)`
    );
    lines.push(`  - Suggestion: ${item.suggestion}`);
  }
  lines.push("");
}

if (totalFindings === 0) {
  lines.push("No issues found. Looks good to merge!");
  lines.push("");
}

lines.push("---");
lines.push("*Generated by [PR Review Agent](https://github.com/airdropia/claude-builders-bounty)*");

const commentBody = lines.join("\n");

console.log("\n=== REVIEW COMMENT ===");
console.log(commentBody);
console.log("=== END ===\n");

if (postComment) {
  try {
    const res = apiPost(
      `/repos/${owner}/${repo}/issues/${prNumber}/comments`,
      { body: commentBody }
    );
    console.log("Comment posted:", res.html_url || res.url);
  } catch (e) {
    console.error("Failed to post comment:", e.message);
    process.exit(1);
  }
} else {
  console.log("Run with --post-comment to post this review to the PR.");
}
