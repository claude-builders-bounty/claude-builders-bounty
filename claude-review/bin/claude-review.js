#!/usr/bin/env node

/**
 * claude-review — AI-powered PR review agent
 *
 * Usage:
 *   claude-review --pr https://github.com/owner/repo/pull/123
 *   claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
 *
 * Environment variables:
 *   ANTHROPIC_API_KEY  — Required. Your Anthropic API key.
 *   GITHUB_TOKEN       — Optional. GitHub token for private repos / higher rate limits.
 */

import { Command } from "commander";
import { parsePrUrl, fetchDiff, fetchPrMeta } from "../src/github.js";
import { analyzeDiff } from "../src/analyzer.js";
import { formatReview } from "../src/formatter.js";
import { writeFileSync } from "node:fs";

const program = new Command();

program
  .name("claude-review")
  .description("AI-powered PR review agent using Claude API")
  .version("1.0.0")
  .requiredOption("--pr <url>", "GitHub Pull Request URL")
  .option("--token <token>", "GitHub token (or set GITHUB_TOKEN env var)")
  .option("--api-key <key>", "Anthropic API key (or set ANTHROPIC_API_KEY env var)")
  .option("--output <file>", "Write review to a file instead of stdout")
  .option("--json", "Output raw JSON analysis instead of Markdown")
  .parse(process.argv);

const opts = program.opts();

async function main() {
  const prUrl = opts.pr;
  const githubToken = opts.token || process.env.GITHUB_TOKEN;
  const apiKey = opts.apiKey || process.env.ANTHROPIC_API_KEY;

  if (!apiKey) {
    console.error(
      "Error: Anthropic API key is required.\n" +
      "Set ANTHROPIC_API_KEY environment variable or pass --api-key <key>"
    );
    process.exit(1);
  }

  // Parse PR URL
  const { owner, repo, pullNumber } = parsePrUrl(prUrl);
  console.error(`🔍 Reviewing PR #${pullNumber} in ${owner}/${repo}...`);

  // Fetch data from GitHub
  console.error("📥 Fetching PR diff and metadata...");
  const [diff, meta] = await Promise.all([
    fetchDiff(owner, repo, pullNumber, githubToken),
    fetchPrMeta(owner, repo, pullNumber, githubToken),
  ]);
  console.error(
    `   ${meta.changedFiles} files changed (+${meta.additions} / -${meta.deletions})`
  );

  // Analyze with Claude
  console.error("🤖 Analyzing with Claude...");
  const review = await analyzeDiff({ diff, meta, apiKey });

  // Format output
  let output;
  if (opts.json) {
    output = JSON.stringify(review, null, 2);
  } else {
    output = formatReview(review, meta, prUrl);
  }

  // Write output
  if (opts.output) {
    writeFileSync(opts.output, output, "utf-8");
    console.error(`✅ Review written to ${opts.output}`);
  } else {
    console.log(output);
  }

  console.error("✅ Done!");
}

main().catch((err) => {
  console.error(`❌ Error: ${err.message}`);
  process.exit(1);
});
