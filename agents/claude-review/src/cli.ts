#!/usr/bin/env node

import { Command } from 'commander';
import { reviewPR } from './reviewer';

const program = new Command();

program
  .name('claude-review')
  .description('Claude Code PR Review Agent')
  .version('1.0.0')
  .requiredOption('--pr <url>', 'GitHub PR URL to review')
  .option('--api-key <key>', 'Anthropic API key (or ANTHROPIC_API_KEY env var)')
  .option('--github-token <token>', 'GitHub token (or GITHUB_TOKEN env var)')
  .action(async (options) => {
    try {
      const result = await reviewPR(options.pr, {
        apiKey: options.apiKey || process.env.ANTHROPIC_API_KEY,
        githubToken: options.githubToken || process.env.GITHUB_TOKEN
      });
      console.log(result);
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

program.parse();