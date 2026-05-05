#!/usr/bin/env node
'use strict';

const { run } = require('../src/index');

function parseArgs(argv) {
  const args = { post: false };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--pr' && argv[i + 1]) {
      args.prUrl = argv[++i];
    } else if (arg === '--post') {
      args.post = true;
    } else if (arg === '--help' || arg === '-h') {
      args.help = true;
    } else if (!arg.startsWith('--')) {
      args.prUrl = arg;
    }
  }

  return args;
}

function printUsage() {
  console.log(`
claude-review — AI-powered PR review via Claude Code

Usage:
  claude-review --pr <github-pr-url> [options]
  claude-review <github-pr-url> [options]

Options:
  --pr <url>    GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)
  --post        Post the review as a comment on the PR (requires GITHUB_TOKEN)
  -h, --help    Show this help message

Environment Variables:
  GITHUB_TOKEN  GitHub personal access token (required for private repos and --post)

Examples:
  claude-review --pr https://github.com/facebook/react/pull/1234
  claude-review https://github.com/owner/repo/pull/42 --post
`);
}

async function main() {
  const args = parseArgs(process.argv);

  if (args.help) {
    printUsage();
    process.exit(0);
  }

  if (!args.prUrl) {
    console.error('Error: PR URL is required. Use --pr <url> or pass the URL directly.');
    console.error('Run with --help for usage information.');
    process.exit(1);
  }

  const token = process.env.GITHUB_TOKEN || '';

  try {
    const comment = await run(args.prUrl, { token, post: args.post });
    console.log(comment);

    if (args.post) {
      console.log('\n✓ Review posted as a comment on the PR.');
    }
  } catch (err) {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  }
}

main();
