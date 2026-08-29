#!/usr/bin/env node

import fs from 'node:fs/promises';
import process from 'node:process';
import { fetchPullRequestInput, upsertPullRequestComment } from '../src/github.mjs';
import { reviewInput } from '../src/reviewer.mjs';

const HELP = `claude-review — structured Claude Code pull-request review

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123 [options]

Required:
  --pr URL                 GitHub pull request URL

Options:
  --post                   Create or update a review comment on the PR (requires GITHUB_TOKEN)
  --output FILE            Also write the Markdown review to FILE
  --json                   Print a JSON envelope instead of raw Markdown
  --model MODEL            Claude Code model alias or full model name
  --max-diff-chars N       Maximum unified-diff characters sent to Claude (default: 150000)
  -h, --help               Show this help
  -v, --version            Show version

Authentication:
  Public PRs can be fetched without GITHUB_TOKEN (subject to GitHub rate limits).
  For private PRs or --post, set GITHUB_TOKEN.
  Claude Code must be installed and authenticated (or ANTHROPIC_API_KEY configured).
`;

function parseArgs(argv) {
  const options = { maxDiffChars: 150_000, json: false, post: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const take = (name) => {
      const value = argv[++i];
      if (!value || value.startsWith('--')) throw new Error(`${name} requires a value`);
      return value;
    };

    switch (arg) {
      case '--pr': options.pr = take('--pr'); break;
      case '--output': options.output = take('--output'); break;
      case '--model': options.model = take('--model'); break;
      case '--max-diff-chars': {
        const value = Number(take('--max-diff-chars'));
        if (!Number.isInteger(value) || value < 2_000) throw new Error('--max-diff-chars must be an integer of at least 2000');
        options.maxDiffChars = value;
        break;
      }
      case '--post': options.post = true; break;
      case '--json': options.json = true; break;
      case '-h': case '--help': options.help = true; break;
      case '-v': case '--version': options.version = true; break;
      default: throw new Error(`Unknown option: ${arg}`);
    }
  }
  return options;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(HELP);
    return;
  }
  if (options.version) {
    process.stdout.write('1.0.0\n');
    return;
  }
  if (!options.pr) throw new Error('--pr is required');

  const prInput = await fetchPullRequestInput(options.pr, {
    token: process.env.GITHUB_TOKEN,
    maxDiffChars: options.maxDiffChars,
  });

  const result = await reviewInput(prInput, { model: options.model });

  if (options.output) {
    await fs.writeFile(options.output, `${result.markdown}\n`, 'utf8');
  }

  let posted = null;
  if (options.post) {
    posted = await upsertPullRequestComment(options.pr, result.markdown, {
      token: process.env.GITHUB_TOKEN,
    });
  }

  if (options.json) {
    process.stdout.write(`${JSON.stringify({
      pullRequest: prInput.source,
      confidence: result.confidence,
      diffTruncated: prInput.diffTruncated,
      posted,
      markdown: result.markdown,
    }, null, 2)}\n`);
  } else {
    process.stdout.write(`${result.markdown}\n`);
    if (posted) process.stderr.write(`Review comment ${posted.action}: ${posted.url}\n`);
  }
}

main().catch((error) => {
  process.stderr.write(`claude-review: ${error.message}\n`);
  process.exitCode = 1;
});
