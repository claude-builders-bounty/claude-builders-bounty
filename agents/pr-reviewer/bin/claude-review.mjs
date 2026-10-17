#!/usr/bin/env node
/**
 * claude-review — analyze a GitHub PR diff and emit a structured review comment.
 *
 *   claude-review --pr https://github.com/owner/repo/pull/123
 *   claude-review --repo owner/repo --number 123 --out review.md
 *   claude-review --pr <url> --post            # also posts via the `gh` CLI
 *   claude-review --pr <url> --fail-on high    # CI gate: exit 1 on High risk
 *
 * Reads GITHUB_TOKEN from the environment if present (raises the rate limit).
 */

import { writeFileSync } from "node:fs";
import { analyzePr, renderMarkdown } from "../src/analyze.mjs";

const HELP = `claude-review — structured review of a GitHub PR diff

Usage:
  claude-review --pr <url> | --repo <owner/name> --number <n> [options]

Options:
  --pr <url>        full PR URL
  --repo <owner/n>  repository
  --number <n>      PR number
  --out <file>      write the markdown here (default: stdout)
  --json            emit JSON instead of markdown
  --post            post the review as a comment using the \`gh\` CLI
  --fail-on <l|m|h> exit 1 when confidence is at or below this level (low|medium|high)
  --no-footer       omit the footer line
  -h, --help        this text
`;

function parseArgs(argv) {
  const a = { flags: new Set() };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === "-h" || k === "--help") a.help = true;
    else if (k === "--json") a.json = true;
    else if (k === "--post") a.post = true;
    else if (k === "--no-footer") a.footer = false;
    else if (k.startsWith("--") && argv[i + 1] !== undefined) a[k.slice(2)] = argv[++i];
  }
  return a;
}

function parsePrUrl(url) {
  const m = /^https?:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/.exec(url || "");
  if (!m) return null;
  return { repo: `${m[1]}/${m[2]}`, number: m[3] };
}

async function api(path, token) {
  const r = await fetch(`https://api.github.com${path}`, {
    headers: {
      accept: "application/vnd.github+json",
      "user-agent": "claude-review",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
  });
  if (!r.ok) throw new Error(`GitHub ${r.status} on ${path}${r.status === 403 || r.status === 404 ? ` (${r.headers.get("x-ratelimit-remaining") ?? "?"} calls left; set GITHUB_TOKEN)` : ""}`);
  return r.json();
}

async function fetchFiles(repo, number, token) {
  const all = [];
  for (let page = 1; page <= 5; page++) {
    const batch = await api(`/repos/${repo}/pulls/${number}/files?per_page=100&page=${page}`, token);
    all.push(...batch);
    if (batch.length < 100) break;
  }
  return all;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || (!args.pr && !args.repo)) {
    process.stdout.write(HELP);
    process.exit(args.help ? 0 : 1);
  }

  const target = args.pr ? parsePrUrl(args.pr) : { repo: args.repo, number: args.number };
  if (!target || !target.repo || !target.number) {
    process.stderr.write("could not determine the PR — pass --pr <url> or --repo <owner/name> --number <n>\n");
    process.exit(1);
  }

  const token = process.env.GITHUB_TOKEN;
  const [pr, files] = await Promise.all([
    api(`/repos/${target.repo}/pulls/${target.number}`, token),
    fetchFiles(target.repo, target.number, token),
  ]);

  const meta = {
    title: pr.title,
    body: pr.body,
    additions: pr.additions,
    deletions: pr.deletions,
    user: pr.user?.login,
    draft: pr.draft,
    url: pr.html_url,
  };

  const result = analyzePr(meta, files);
  const rank = { Low: 0, Medium: 1, High: 2 };
  const risky = result.confidence === "Low" || result.risks.length >= 3;

  const output = args.json
    ? JSON.stringify({ pr: meta, files: files.length, ...result }, null, 2)
    : renderMarkdown(meta, files, result, { footer: args.footer });

  if (args.out) {
    writeFileSync(args.out, output);
    process.stderr.write(`wrote ${args.out} (confidence ${result.confidence}, ${result.risks.length} risk(s))\n`);
  } else if (!args.post) {
    process.stdout.write(output + "\n");
  }

  if (args.post) {
    const body = args.out || `/tmp/claude-review-${target.number}.md`;
    if (!args.out) writeFileSync(body, output);
    const { spawnSync } = await import("node:child_process");
    const r = spawnSync("gh", ["pr", "comment", String(target.number), "--repo", target.repo, "--body-file", body], {
      stdio: "inherit",
    });
    if (r.status !== 0) process.exit(r.status ?? 1);
  }

  if (args["fail-on"] && rank[result.confidence] <= rank[args["fail-on"]]) {
    process.stderr.write(`confidence ${result.confidence} is at or below --fail-on ${args["fail-on"]}\n`);
    process.exit(1);
  }
  if (risky && args.json) process.exit(0);
}

main().catch((e) => {
  process.stderr.write(`claude-review: ${e.message}\n`);
  process.exit(1);
});
