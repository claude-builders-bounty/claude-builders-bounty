#!/usr/bin/env node

/**
 * claude-review — AI-powered PR review agent
 *
 * Usage:
 *   npx claude-review --pr https://github.com/owner/repo/pull/123
 *   npx claude-review --pr owner/repo#123
 *   npx claude-review --pr 123 --repo owner/repo
 *
 * Requires:
 *   - GITHUB_TOKEN (or GH_TOKEN) env var with repo scope
 *   - ANTHROPIC_API_KEY env var
 */

import { execSync } from "node:child_process";
import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";

// ─── Argument Parsing ────────────────────────────────────────────────

function parseArgs(argv) {
  const args = { pr: null, repo: null, output: null, post: false };
  for (let i = 2; i < argv.length; i++) {
    switch (argv[i]) {
      case "--pr":    args.pr = argv[++i]; break;
      case "--repo":  args.repo = argv[++i]; break;
      case "--output": args.output = argv[++i]; break;
      case "--post":  args.post = true; break;
      case "--help":
        console.log(`Usage: claude-review --pr <url|number> [--repo owner/repo] [--output dir] [--post]

Options:
  --pr      PR URL, owner/repo#123, or issue number
  --repo    Repository (required if --pr is just a number)
  --output  Output directory for review files (default: ./reviews)
  --post    Post the review as a PR comment
  --help    Show this help
`);
        process.exit(0);
      default:
        console.error(`Unknown argument: ${argv[i]}`);
        process.exit(1);
    }
  }
  return args;
}

// ─── PR URL / Reference Parsing ──────────────────────────────────────

function parsePrRef(pr, repo) {
  // Full URL: https://github.com/owner/repo/pull/123
  const urlMatch = pr?.match(/github\.com\/([^/]+\/[^/]+)\/pull\/(\d+)/);
  if (urlMatch) return { repo: urlMatch[1], number: parseInt(urlMatch[2]) };

  // Shorthand: owner/repo#123
  const shortMatch = pr?.match(/^([^/]+\/[^/]+)#(\d+)$/);
  if (shortMatch) return { repo: shortMatch[1], number: parseInt(shortMatch[2]) };

  // Just a number
  if (/^\d+$/.test(pr) && repo) return { repo, number: parseInt(pr) };

  throw new Error(`Cannot parse PR reference: ${pr}. Use full URL, owner/repo#123, or number with --repo.`);
}

// ─── GitHub API Helpers ──────────────────────────────────────────────

function gh(apiPath) {
  const result = execSync(`gh api ${apiPath}`, { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] });
  return JSON.parse(result);
}

function getPrDiff(repo, number) {
  return execSync(`gh api repos/${repo}/pulls/${number} --header "Accept: application/vnd.diff"`, {
    encoding: "utf-8",
    stdio: ["pipe", "pipe", "pipe"]
  });
}

function getPrInfo(repo, number) {
  return gh(`repos/${repo}/pulls/${number}`);
}

function getPrFiles(repo, number) {
  return gh(`repos/${repo}/pulls/${number}/files`);
}

function postComment(repo, number, body) {
  execSync(`gh api repos/${repo}/issues/${number}/comments -f body="${body.replace(/"/g, '\\"').replace(/`/g, '\\`')}"`, {
    encoding: "utf-8",
    stdio: ["pipe", "pipe", "pipe"]
  });
}

// ─── Claude API Call ─────────────────────────────────────────────────

function callClaude(diff, prInfo, files) {
  const fileList = files.map(f => `- \`${f.filename}\` (${f.status}, +${f.additions}/-${f.deletions})`).join("\n");

  const prompt = `You are an expert code reviewer. Analyze the following pull request and produce a structured Markdown review.

## PR Information
- **Title**: ${prInfo.title}
- **Author**: ${prInfo.user?.login}
- **Base**: ${prInfo.base?.ref} ← **Head**: ${prInfo.head?.ref}
- **Changed files** (${files.length}):
${fileList}

## Diff
\`\`\`diff
${diff.slice(0, 50000)}
\`\`\`

## Required Output Format

Produce EXACTLY this Markdown structure:

# PR Review: ${prInfo.title}

## 📋 Summary
(2–3 sentences summarizing what this PR does and why)

## ⚠️ Risks
(Enumerated list of potential issues, bugs, security concerns, or breaking changes. Use \`code\` references.)

## 💡 Suggestions
(Enumerated list of concrete improvement ideas. Be specific — reference file names and line patterns.)

## 🎯 Confidence: Low / Medium / High
(One word only. Based on how well you understand the changes and how many risks you found.)

Rules:
- Be concise but thorough
- Focus on correctness, security, and maintainability
- If the diff is trivial, say so and keep the review short
- Always include all 4 sections even if some are empty lists`;

  const body = {
    model: "claude-sonnet-4-20250514",
    max_tokens: 4096,
    messages: [{ role: "user", content: prompt }]
  };

  const response = execSync(`curl -s https://api.anthropic.com/v1/messages \
    -H "Content-Type: application/json" \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -d '${JSON.stringify(body).replace(/'/g, "'\"'\"'")}'`, {
    encoding: "utf-8",
    stdio: ["pipe", "pipe", "pipe"]
  });

  const result = JSON.parse(response);
  if (result.error) throw new Error(`Claude API error: ${result.error.message}`);
  return result.content[0].text;
}

// ─── Main ────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs(process.argv);

  if (!args.pr) {
    console.error("Error: --pr is required. Use --help for usage.");
    process.exit(1);
  }

  const { repo, number } = parsePrRef(args.pr, args.repo);
  console.log(`🔍 Reviewing PR #${number} in ${repo}...`);

  // Fetch PR data
  const [prInfo, diff, files] = await Promise.all([
    getPrInfo(repo, number),
    getPrDiff(repo, number),
    getPrFiles(repo, number)
  ]);

  console.log(`📄 ${prInfo.title}`);
  console.log(`📊 ${files.length} files changed, diff size: ${(diff.length / 1024).toFixed(1)}KB`);

  if (!diff.trim()) {
    console.log("⚠️ Empty diff — nothing to review.");
    process.exit(0);
  }

  // Call Claude for review
  console.log("🤖 Calling Claude for review...");
  const review = callClaude(diff, prInfo, files);

  // Save to file
  const outputDir = args.output || "./reviews";
  if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

  const filename = `review-${repo.replace("/", "-")}-${number}.md`;
  const outputPath = join(outputDir, filename);
  writeFileSync(outputPath, review);
  console.log(`✅ Review saved to ${outputPath}`);

  // Print to stdout
  console.log("\n" + "=".repeat(60));
  console.log(review);
  console.log("=".repeat(60) + "\n");

  // Post as comment if requested
  if (args.post) {
    console.log("📝 Posting review as PR comment...");
    postComment(repo, number, review);
    console.log("✅ Comment posted!");
  }
}

main().catch(err => {
  console.error("❌ Error:", err.message);
  process.exit(1);
});
