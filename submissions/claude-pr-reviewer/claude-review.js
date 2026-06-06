#!/usr/bin/env node
/**
 * claude-review — Claude Code sub-agent for PR review
 * 
 * Usage:
 *   claude-review --pr https://github.com/owner/repo/pull/123
 *   claude-review --diff /path/to/diff.patch
 *   GITHUB_TOKEN=... claude-review --pr https://github.com/owner/repo/pull/123
 */

import { reviewPR } from '../lib/reviewer.js';

const args = process.argv.slice(2);
const prIndex = args.indexOf('--pr');
const diffIndex = args.indexOf('--diff');

if (prIndex !== -1 && args[prIndex + 1]) {
  const prUrl = args[prIndex + 1];
  reviewPR({ prUrl }).then(output => {
    console.log(output);
  }).catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
  });
} else if (diffIndex !== -1 && args[diffIndex + 1]) {
  const diffPath = args[diffIndex + 1];
  reviewPR({ diffPath }).then(output => {
    console.log(output);
  }).catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
  });
} else {
  console.log(`claude-review — PR Review Agent

Usage:
  claude-review --pr <github-pr-url>    Review a GitHub PR
  claude-review --diff <patch-file>     Review a local diff file

Environment:
  GITHUB_TOKEN    GitHub token for API access (required for --pr mode)
`);
}
