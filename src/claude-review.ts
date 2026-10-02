#!/usr/bin/env node

import { Command } from 'commander';
import { fetchPRDiff } from './github-api';
import { analyzePR } from './pr-analyzer';
import { generateMarkdownReview } from './markdown-generator';

const program = new Command();

program
  .name('claude-review')
  .description('PR review agent for Claude Code')
  .version('1.0.0')
  .argument('<pr-url>', 'GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)')
  .action(async (prUrl: string) => {
    try {
      // Extract owner, repo, and PR number from URL
      const match = prUrl.match(/github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/);
      if (!match) {
        console.error('Invalid GitHub PR URL format. Please use: https://github.com/owner/repo/pull/123');
        process.exit(1);
      }

      const [, owner, repo, prNumber] = match;
      console.log(`Analyzing PR #${prNumber} in ${owner}/${repo}...`);

      // Fetch PR diff
      const diff = await fetchPRDiff(owner, repo, parseInt(prNumber));
      
      // Analyze PR using Claude
      const analysis = await analyzePR(diff, prUrl);
      
      // Generate markdown review
      const review = generateMarkdownReview(analysis);
      
      // Output the review
      console.log('\n=== PR REVIEW ===');
      console.log(review);
      
      // If we're in a CI environment, write to file for GitHub Action
      if (process.env.GITHUB_ACTIONS) {
        require('fs').writeFileSync(process.env.GITHUB_STEP_SUMMARY, review);
      }
    } catch (error) {
      console.error('Error analyzing PR:', error);
      process.exit(1);
    }
  });

program.parse();