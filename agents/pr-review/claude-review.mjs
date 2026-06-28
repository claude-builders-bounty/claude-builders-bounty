#!/usr/bin/env node

/**
 * claude-review — PR review sub-agent for Claude Code
 *
 * Usage:
 *   node claude-review.mjs --pr https://github.com/owner/repo/pull/123
 *   node claude-review.mjs --diff /path/to/diff.txt
 *
 * Output: Structured Markdown review with:
 *   - Summary of changes
 *   - Identified risks
 *   - Improvement suggestions
 *   - Confidence score
 */

import { execSync } from "child_process";
import { readFileSync, writeFileSync, existsSync } from "fs";
import { homedir } from "os";
import { resolve } from "path";

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || "";
const CLAUDE_BIN = process.env.CLAUDE_BIN || "claude";
const CONFIG_PATH = resolve(homedir(), ".claude-review.json");

let userConfig = {};
if (existsSync(CONFIG_PATH)) {
  try { userConfig = JSON.parse(readFileSync(CONFIG_PATH, "utf-8")); } catch {}
}

const config = {
  model: "claude-sonnet-4-20250514",
  maxTokens: 4096,
  temperature: 0.3,
  ...userConfig,
};

function printHelp() {
  console.log(`
claude-review — AI-powered PR review sub-agent

USAGE:
  node claude-review.mjs --pr <pr-url>       Review a GitHub PR
  node claude-review.mjs --diff <file>       Review a local diff file
  node claude-review.mjs --help              Show this help

OPTIONS:
  --pr         GitHub PR URL
  --diff       Path to a local diff/patch file
  --output     Output file path (default: stdout)
  --no-post    Don't post review as comment on the PR

ENVIRONMENT:
  GITHUB_TOKEN   GitHub PAT (required for --pr)
`);
}

async function ghFetch(url) {
  const resp = await fetch(url, {
    headers: {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
      Accept: "application/vnd.github.v3.diff",
      "User-Agent": "claude-review",
    },
  });
  if (!resp.ok) throw new Error(`GitHub error ${resp.status}: ${resp.statusText}`);
  return resp;
}

async function ghFetchJSON(url) {
  const resp = await fetch(url, {
    headers: {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
      Accept: "application/vnd.github.v3+json",
      "User-Agent": "claude-review",
    },
  });
  if (!resp.ok) throw new Error(`GitHub error ${resp.status}: ${resp.statusText}`);
  return resp.json();
}

function parsePRUrl(url) {
  const m = url.match(/github\.com\/([^/]+)\/([^/]+?)\/pull\/(\d+)/);
  if (!m) throw new Error(`Invalid PR URL: ${url}`);
  return { owner: m[1], repo: m[2].replace(/\.git$/, ""), pr: parseInt(m[3]) };
}

async function fetchPRDiff(prUrl) {
  const { owner, repo, pr } = parsePRUrl(prUrl);
  const apiUrl = `https://api.github.com/repos/${owner}/${repo}/pulls/${pr}`;
  const resp = await ghFetch(apiUrl);
  return { diff: await resp.text(), owner, repo, pr };
}

function generateReview(diffContent) {
  const MAX_LEN = 80000;
  const truncated = diffContent.length > MAX_LEN
    ? diffContent.slice(0, MAX_LEN) + "\n\n...[truncated]"
    : diffContent;

  const prompt = `You are a senior engineer doing a code review.

Analyze this PR diff and produce a structured Markdown review with:

### Summary of Changes
2-3 sentences about what this PR does.

### Identified Risks
- Specific bugs, regressions, security or performance issues
- Reference specific lines or patterns

### Improvement Suggestions
- Actionable improvements with code examples where helpful
- Prioritized by importance

### Confidence Score
**Low** / **Medium** / **High**

\`\`\`diff
${truncated}
\`\`\`
`;

  const tmpFile = resolve(homedir(), ".claude-review-prompt.md");
  writeFileSync(tmpFile, prompt, "utf-8");
  try {
    const stdout = execSync(
      `${CLAUDE_BIN} --model ${config.model} --max-tokens ${config.maxTokens} -f "${tmpFile}" --print`,
      { encoding: "utf-8", maxBuffer: 10 * 1024 * 1024, timeout: 120000 }
    );
    try { execSync(`rm "${tmpFile}"`); } catch {}
    return stdout.trim();
  } catch (err) {
    if (err.stdout) return err.stdout.trim();
    throw new Error(`Claude execution failed: ${err.message}`);
  }
}

async function postComment(owner, repo, pr, body) {
  const url = `https://api.github.com/repos/${owner}/${repo}/issues/${pr}/comments`;
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "claude-review",
    },
    body: JSON.stringify({
      body: `## 🤖 AI-Powered PR Review\n\n${body}\n\n---\n*Review by claude-review*`,
    }),
  });
  if (!resp.ok) throw new Error(`Post comment failed: ${resp.status}`);
  return (await resp.json()).html_url;
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--help") || args.length === 0) { printHelp(); process.exit(0); }

  let diffContent, prInfo = null, outputPath = null, shouldPost = true;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--pr" && args[i+1]) { prInfo = await fetchPRDiff(args[++i]); diffContent = prInfo.diff; }
    else if (args[i] === "--diff" && args[i+1]) { diffContent = readFileSync(resolve(args[++i]), "utf-8"); }
    else if (args[i] === "--output" && args[i+1]) { outputPath = args[++i]; }
    else if (args[i] === "--no-post") { shouldPost = false; }
  }

  if (!diffContent) { console.error("No diff provided"); process.exit(1); }

  process.stderr.write("Generating review...\n");
  const review = generateReview(diffContent);
  const full = `## 🤖 AI-Powered PR Review\n\n${review}`;

  if (outputPath) {
    writeFileSync(resolve(outputPath), full, "utf-8");
    console.error(`Written to ${outputPath}`);
  } else {
    console.log(full);
  }

  if (prInfo && shouldPost && GITHUB_TOKEN) {
    try {
      const url = await postComment(prInfo.owner, prInfo.repo, prInfo.pr, review);
      console.error(`Posted: ${url}`);
    } catch (e) { console.error(`Comment failed: ${e.message}`); }
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
