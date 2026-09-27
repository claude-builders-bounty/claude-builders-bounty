#!/usr/bin/env node
import { Command } from 'commander';
import dotenv from 'dotenv';
import ora from 'ora';
import fs from 'fs';
import { GitHubService } from './github.js';
import { reviewPR } from './analyzer.js';
import { formatReview } from './formatter.js';
import { ReviewConfig } from './types.js';

dotenv.config();

const program = new Command();

program
  .name('claude-review')
  .description('Review GitHub Pull Requests using Claude API')
  .version('1.0.0')
  .requiredOption('--pr <url>', 'GitHub PR URL to review (e.g. https://github.com/owner/repo/pull/123)')
  .option('--depth <level>', 'Review depth: quick, standard, or deep', 'standard')
  .option('--format <type>', 'Output format: console, markdown, or json', 'console')
  .option('--output <file>', 'Save output to file')
  .option('--post-comment', 'Post review as a PR comment')
  .option('--verbose', 'Enable verbose logging')
  .action(async (options) => {
    try {
      const config: ReviewConfig = {
        depth: options.depth as 'quick' | 'standard' | 'deep',
        format: options.format as 'console' | 'markdown' | 'json',
        postComment: options.postComment || false,
        verbose: options.verbose || false,
        outputFile: options.output,
      };

      const githubToken = process.env.GITHUB_TOKEN;
      const anthropicKey = process.env.ANTHROPIC_API_KEY;

      if (!githubToken) {
        throw new Error('GITHUB_TOKEN environment variable is missing');
      }
      if (!anthropicKey) {
        throw new Error('ANTHROPIC_API_KEY environment variable is missing');
      }

      const github = new GitHubService(githubToken);

      const spinner = ora('Parsing PR URL').start();
      const { owner, repo, number } = github.parsePRUrl(options.pr);
      
      spinner.text = 'Fetching PR details';
      const prInfo = await github.getPRInfo(owner, repo, number);
      
      spinner.text = 'Fetching PR diff';
      const prDiff = await github.getPRDiff(owner, repo, number);

      spinner.text = 'Analyzing with Claude';
      const review = await reviewPR(prInfo, prDiff, config, anthropicKey);

      spinner.succeed('Analysis complete');

      const formattedOutput = formatReview(prInfo, prDiff, review, config);

      if (config.outputFile) {
        fs.writeFileSync(config.outputFile, formattedOutput, 'utf-8');
        console.log(`\nOutput saved to ${config.outputFile}`);
      } else {
        console.log(formattedOutput);
      }

      if (config.postComment) {
        const commentSpinner = ora('Posting comment to PR').start();
        const markdownOutput = formatReview(prInfo, prDiff, review, { ...config, format: 'markdown' });
        await github.postComment(owner, repo, number, markdownOutput);
        commentSpinner.succeed('Comment posted successfully');
      }

    } catch (error: any) {
      console.error(`\nError: ${error.message}`);
      process.exit(1);
    }
  });

program.parse(process.argv);
