#!/usr/bin/env node
/**
 * weekly-dev-summary.js - Generate weekly dev summary from git history
 * and post to n8n webhook.
 *
 * Usage:
 *   node weekly-dev-summary.js --webhook-url <url> [--days 7] [--post]
 *
 * Environment:
 *   GITHUB_TOKEN     GitHub PAT for PR metadata (optional)
 *   N8N_WEBHOOK_URL  n8n webhook URL (optional, can use --webhook-url)
 */

import { execSync } from "node:child_process";
import { writeFileSync, readFileSync, existsSync } from "node:fs";

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL;

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--webhook-url" && i + 1 < argv.length) args.webhookUrl = argv[++i];
    else if (a === "--days" && i + 1 < argv.length) args.days = parseInt(argv[++i], 10);
    else if (a === "--post") args.post = true;
    else if (a === "--help" || a === "-h") {
      console.log("Usage: node weekly-dev-summary.js --webhook-url <url> [--days 7] [--post]");
      process.exit(0);
    }
  }
  return args;
}

const { webhookUrl, days = 7, post } = parseArgs(process.argv);

const webhook = webhookUrl || N8N_WEBHOOK_URL;
if (!webhook && post) {
  console.error("ERROR: --webhook-url or N8N_WEBHOOK_URL required for --post");
  process.exit(1);
}

// Calculate date range
const now = new Date();
const since = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
const sinceStr = since.toISOString().split("T")[0];
const untilStr = now.toISOString().split("T")[0];

// Fetch git log
let logOutput = "";
try {
  logOutput = execSync(
    `git log --since="${sinceStr}" --until="${untilStr}" --pretty="format:%s%x01%an%x01%ad%x01%h" --date=short`,
    { encoding: "utf8" }
  ).trim();
} catch (e) {
  console.error("ERROR: Failed to read git log:", e.message);
  process.exit(1);
}

const lines = logOutput.split("\n").filter((l) => l.trim());

// Categorize
const categories = {
  feat: { title: "🚀 Added", items: [], count: 0 },
  fix: { title: "🐛 Fixed", items: [], count: 0 },
  docs: { title: "📝 Changed", items: [], count: 0 },
  style: { title: "📝 Changed", items: [], count: 0 },
  refactor: { title: "📝 Changed", items: [], count: 0 },
  perf: { title: "⚡ Improved", items: [], count: 0 },
  test: { title: "🧪 Tested", items: [], count: 0 },
  build: { title: "🧹 Chore", items: [], count: 0 },
  ci: { title: "🧹 Chore", items: [], count: 0 },
  chore: { title: "🧹 Chore", items: [], count: 0 },
};

const contributors = {};
let totalCommits = 0;
let totalFiles = new Set();

for (const line of lines) {
  const parts = line.split("\u0001");
  const msg = parts[0] || "";
  const author = parts[1] || "unknown";
  const date = parts[2] || "";
  const hash = parts[3] || "";

  totalCommits++;
  contributors[author] = (contributors[author] || 0) + 1;

  // Get files changed in this commit
  try {
    const files = execSync(`git show --name-only --format="" ${hash}`, {
      encoding: "utf8",
    }).trim().split("\n").filter(f => f.trim());
    for (const f of files) totalFiles.add(f);
  } catch {
    // ignore
  }

  const lower = msg.toLowerCase();
  let categorized = false;
  for (const [prefix, cat] of Object.entries(categories)) {
    if (lower.startsWith(`${prefix}:`)) {
      cat.items.push(`- ${msg} (@${author})`);
      cat.count++;
      categorized = true;
      break;
    }
  }
  if (!categorized) {
    categories.chore.items.push(`- ${msg} (@${author})`);
    categories.chore.count++;
  }
}

// Fetch merged PRs if GitHub token available
let prs = [];
if (GITHUB_TOKEN) {
  try {
    const remoteUrl = execSync("git remote get-url origin", { encoding: "utf8" }).trim();
    const m = remoteUrl.match(/github\.com[:/]([^/]+)\/([^/]+?)(?:\.git)?$/);
    if (m) {
      const [, owner, repo] = m;
      const prsRaw = execSync(
        `curl -s -H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/${owner}/${repo}/pulls?state=closed&sort=updated&direction=desc&per_page=20"`,
        { encoding: "utf8" }
      );
      const parsed = JSON.parse(prsRaw);
      const sinceDate = new Date(sinceStr);
      for (const pr of parsed) {
        if (pr.merged_at && new Date(pr.merged_at) >= sinceDate) {
          prs.push({ number: pr.number, title: pr.title, author: pr.user.login, url: pr.html_url });
        }
      }
    }
  } catch {
    // ignore PR fetch errors
  }
}

// Build summary
const out = [];
out.push(`# Weekly Dev Summary — ${sinceStr} to ${untilStr}`);
out.push("");
out.push("## Overview");
out.push(`- ${totalCommits} commits across ${totalFiles.size} files`);
out.push(`- ${Object.keys(contributors).length} contributors`);
if (prs.length) out.push(`- ${prs.length} merged PRs`);
out.push("");

out.push("## Commits by Type");
const totalCat = Object.values(categories).reduce((s, c) => s + c.count, 0);
for (const [key, cat] of Object.entries(categories)) {
  if (cat.count === 0) continue;
  const pct = totalCat > 0 ? Math.round((cat.count / totalCat) * 100) : 0;
  out.push(`- ${cat.title}: ${cat.count} (${pct}%)`);
}
out.push("");

out.push("## Top Contributors");
const sortedContributors = Object.entries(contributors).sort((a, b) => b[1] - a[1]);
for (const [author, count] of sortedContributors.slice(0, 10)) {
  out.push(`- @${author} — ${count} commits`);
}
out.push("");

if (prs.length) {
  out.push("## Merged PRs");
  for (const pr of prs.slice(0, 10)) {
    out.push(`- #${pr.number}: ${pr.title} (@${pr.author})`);
  }
  out.push("");
}

out.push("## Notable Changes");
const notable = [...categories.feat.items, ...categories.fix.items].slice(0, 8);
if (notable.length) {
  for (const item of notable) out.push(`- ${item.slice(2)}`);
} else {
  out.push("- No notable feature or fix commits this week.");
}
out.push("");

out.push("---");
out.push("*Generated by Weekly Dev Summary Agent*");

const summary = out.join("\n");
console.log(summary);

if (post && webhook) {
  try {
    const res = execSync(
      `curl -s -X POST -H "Content-Type: application/json" -d '${JSON.stringify({ text: summary })}' "${webhook}"`,
      { encoding: "utf8" }
    );
    console.log("\n✓ Posted to n8n webhook");
  } catch (e) {
    console.error("\n✗ Failed to post to webhook:", e.message);
    process.exit(1);
  }
}
