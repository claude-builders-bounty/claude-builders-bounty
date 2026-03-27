#!/usr/bin/env node

import { Command } from 'commander';
import { GitHubClient } from './github';
import { ClaudeReviewer } from './reviewer';
import { formatReviewAsMarkdown, printReviewToConsole } from './formatter';
import * as fs from 'fs';
import * as path from 'path';
import 'dotenv/config';

const program = new Command();

program
  .name('claude-review')
  .description('Claude Code sub-agent that reviews GitHub PRs and posts structured comments')
  .version('1.0.0')
  .requiredOption('-p, --pr <url>', 'GitHub PR URL to review')
  .option('-o, --output <format>', 'Output format (markdown, json, console)', 'console')
  .option('-f, --file <path>', 'Save output to file')
  .option('-v, --verbose', 'Show verbose output', false);

async function main() {
  program.parse(process.argv);
  const options = program.opts();

  const githubToken = process.env.GITHUB_TOKEN;
  const claudeApiKey = process.env.ANTHROPIC_API_KEY;

  if (!githubToken) {
    console.error('❌ Error: GITHUB_TOKEN environment variable is required');
    console.error('   Get your token from: https://github.com/settings/tokens');
    process.exit(1);
  }

  if (!claudeApiKey) {
    console.error('❌ Error: ANTHROPIC_API_KEY environment variable is required');
    console.error('   Get your API key from: https://console.anthropic.com/');
    process.exit(1);
  }

  try {
    const github = new GitHubClient(githubToken);
    const reviewer = new ClaudeReviewer(claudeApiKey);

    // Parse PR URL
    console.log(`🔍 Fetching PR: ${options.pr}`);
    const { owner, repo, number } = github.parsePRUrl(options.pr);

    // Fetch PR info and diff
    console.log(`📥 Fetching PR info and diff...`);
    const [prInfo, diff] = await Promise.all([
      github.getPRInfo(owner, repo, number),
      github.getPRDiff(owner, repo, number)
    ]);

    if (options.verbose) {
      console.log(`\n📋 PR Info:`);
      console.log(`   Title: ${prInfo.title}`);
      console.log(`   Author: ${prInfo.author}`);
      console.log(`   Branch: ${prInfo.headBranch} → ${prInfo.baseBranch}`);
      console.log(`   Files: ${prInfo.files.length} changed`);
    }

    // Perform review
    console.log(`🤖 Analyzing PR with Claude...`);
    const review = await reviewer.reviewPR(prInfo, diff);

    // Output results
    let output: string;
    
    switch (options.output) {
      case 'markdown':
        output = formatReviewAsMarkdown(prInfo, review);
        break;
      case 'json':
        output = JSON.stringify({
          pr: prInfo,
          review: {
            summary: review.summary,
            risks: review.risks,
            suggestions: review.suggestions,
            confidence: review.confidence
          }
        }, null, 2);
        break;
      case 'console':
      default:
        printReviewToConsole(prInfo, review);
        output = formatReviewAsMarkdown(prInfo, review);
    }

    // Save to file if requested
    if (options.file) {
      const filePath = path.resolve(options.file);
      fs.writeFileSync(filePath, output, 'utf-8');
      console.log(`\n✅ Review saved to: ${filePath}`);
    }

    // Exit with appropriate code based on confidence
    const exitCodes = { 'Low': 1, 'Medium': 0, 'High': 0 };
    process.exit(exitCodes[review.confidence]);

  } catch (error) {
    console.error(`\n❌ Error: ${error instanceof Error ? error.message : error}`);
    if (options.verbose && error instanceof Error && error.stack) {
      console.error('\nStack trace:');
      console.error(error.stack);
    }
    process.exit(1);
  }
}

main();
