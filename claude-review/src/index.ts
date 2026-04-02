#!/usr/bin/env node

import { fetchPRInfo, parsePRUrl, postPRComment } from "./github.js";
import { reviewPR, formatReviewAsMarkdown } from "./reviewer.js";

interface CLIOptions {
  prUrl?: string;
  post?: boolean;
  token?: string;
}

function parseArgs(args: string[]): CLIOptions {
  const options: CLIOptions = {};
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg === "--pr" || arg === "-p") {
      options.prUrl = args[++i];
    } else if (arg === "--post" || arg === "-c") {
      options.post = true;
    } else if (arg === "--token" || arg === "-t") {
      options.token = args[++i];
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else if (!arg.startsWith("-")) {
      // Assume it's the PR URL if no flag
      options.prUrl = arg;
    }
  }
  
  return options;
}

function printHelp(): void {
  console.log(`
claude-review - AI-powered PR review tool

USAGE:
  claude-review --pr <url> [options]
  claude-review <url> [options]

OPTIONS:
  --pr, -p <url>      GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)
  --post, -c          Post the review as a comment on the PR
  --token, -t <token> GitHub token (or set GITHUB_TOKEN env var)
  --help, -h          Show this help message

EXAMPLES:
  # Review a PR and print to stdout
  claude-review --pr https://github.com/owner/repo/pull/123
  
  # Review and post comment
  claude-review --pr https://github.com/owner/repo/pull/123 --post
  
  # With explicit token
  claude-review --pr https://github.com/owner/repo/pull/123 --post --token ghp_xxx

ENVIRONMENT:
  GITHUB_TOKEN    GitHub personal access token
  ANTHROPIC_API_KEY  Anthropic API key for Claude

OUTPUT FORMAT:
  - Summary of changes (2-3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High
`);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const options = parseArgs(args);

  if (!options.prUrl) {
    console.error("Error: PR URL is required");
    console.error("Use --help for usage information");
    process.exit(1);
  }

  // Validate URL
  try {
    parsePRUrl(options.prUrl);
  } catch (e) {
    console.error(`Error: Invalid PR URL: ${options.prUrl}`);
    process.exit(1);
  }

  // Check for required API keys
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("Error: ANTHROPIC_API_KEY environment variable is required");
    console.error("Get your key at: https://console.anthropic.com/");
    process.exit(1);
  }

  console.log("🔍 Fetching PR information...");
  const prInfo = await fetchPRInfo(options.prUrl, options.token);
  console.log(`📋 PR #${prInfo.prNumber}: ${prInfo.title}`);
  console.log(`   Author: ${prInfo.author}`);
  console.log(`   Files: ${prInfo.files.length} | +${prInfo.additions} / -${prInfo.deletions}`);

  console.log("\n🤖 Analyzing with Claude...");
  const review = await reviewPR(prInfo);

  const markdownOutput = formatReviewAsMarkdown(prInfo, review);
  console.log("\n" + markdownOutput);

  if (options.post) {
    if (!options.token && !process.env.GITHUB_TOKEN) {
      console.error("\n⚠️  Warning: GITHUB_TOKEN not set. Cannot post comment.");
      console.error("   Set the GITHUB_TOKEN environment variable or use --token");
    } else {
      console.log("\n💬 Posting review as PR comment...");
      await postPRComment(options.prUrl, markdownOutput, options.token);
      console.log("✅ Comment posted successfully!");
    }
  }

  // Exit with confidence-based code for CI/CD
  if (review.confidence === "Low") {
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("Error:", error.message || error);
  process.exit(1);
});
