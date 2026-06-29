#!/usr/bin/env node

/**
 * claude-review — Claude Code sub-agent for PR reviews.
 *
 * 跑起来吧：`claude-review --pr https://github.com/owner/repo/pull/123`
 * 它会拉 diff，扔给 Claude 分析，吐出一份漂亮的结构化 review。
 */

import { Command } from 'commander';
import { reviewPR } from './reviewer.js';

const program = new Command();

program
  .name('claude-review')
  .description('Claude Code sub-agent that reviews a PR and outputs structured Markdown')
  .version('1.0.0')
  .requiredOption('--pr <url>', 'Full URL of the PR to review (e.g. https://github.com/owner/repo/pull/123)')
  .option('--model <name>', 'Claude model to use', 'claude-sonnet-4-20250514')
  .option('--max-tokens <number>', 'Max tokens for the response', '4096')
  .option('--output <file>', 'Write review to file instead of stdout')
  .option('--gh-token <token>', 'GitHub token (or set GITHUB_TOKEN env var)')
  .option('--anthropic-key <key>', 'Anthropic API key (or set ANTHROPIC_API_KEY env var)')
  .parse(process.argv);

const opts = program.opts();

const ghToken = opts.ghToken || process.env.GITHUB_TOKEN;
if (!ghToken) {
  console.error('❌ GitHub token required. Pass --gh-token or set GITHUB_TOKEN env var.');
  process.exit(1);
}

const anthropicKey = opts.anthropicKey || process.env.ANTHROPIC_API_KEY;
if (!anthropicKey) {
  console.error('❌ Anthropic API key required. Pass --anthropic-key or set ANTHROPIC_API_KEY env var.');
  process.exit(1);
}

const result = await reviewPR({
  prUrl: opts.pr,
  ghToken,
  anthropicKey,
  model: opts.model,
  maxTokens: parseInt(opts.maxTokens, 10),
});

if (opts.output) {
  const fs = await import('fs');
  fs.writeFileSync(opts.output, result, 'utf-8');
  console.log(`✅ Review written to ${opts.output}`);
} else {
  console.log(result);
}
