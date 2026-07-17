#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { analyzeDiff, formatReview, parseGitHubPullRequestUrl } from '../lib/review.js';

const args = process.argv.slice(2);

function help() {
  return `claude-review

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --diff-file path/to/pr.diff
  claude-review --stdin < pr.diff

Options:
  --pr          GitHub pull request URL to review
  --diff-file   Local unified diff file to review
  --stdin       Read a unified diff from stdin
  --json        Print the structured review object as JSON
  --help        Show this help

Environment:
  GITHUB_TOKEN  Optional token for private repos or higher API limits
`;
}

function valueAfter(flag) {
  const index = args.indexOf(flag);
  if (index === -1) return undefined;
  return args[index + 1];
}

function readStdin() {
  return readFileSync(0, 'utf8');
}

async function fetchPrDiff(prUrl) {
  const parsed = parseGitHubPullRequestUrl(prUrl);
  if (!parsed) {
    throw new Error(`Invalid GitHub pull request URL: ${prUrl}`);
  }

  const ghResult = spawnSync('gh', ['pr', 'diff', prUrl], { encoding: 'utf8' });
  if (ghResult.status === 0 && ghResult.stdout.trim()) {
    return ghResult.stdout;
  }

  const headers = {
    Accept: 'application/vnd.github.v3.diff',
    'User-Agent': 'claude-review-agent'
  };
  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  const response = await fetch(
    `https://api.github.com/repos/${parsed.owner}/${parsed.repo}/pulls/${parsed.pullNumber}`,
    { headers }
  );
  if (!response.ok) {
    throw new Error(`Could not fetch PR diff: ${response.status} ${response.statusText}`);
  }
  return response.text();
}

async function main() {
  if (args.includes('--help') || args.length === 0) {
    process.stdout.write(help());
    return;
  }

  let diff;
  const prUrl = valueAfter('--pr');
  const diffFile = valueAfter('--diff-file');

  if (prUrl) {
    diff = await fetchPrDiff(prUrl);
  } else if (diffFile) {
    diff = readFileSync(diffFile, 'utf8');
  } else if (args.includes('--stdin')) {
    diff = readStdin();
  } else {
    throw new Error('Provide --pr, --diff-file, or --stdin. Use --help for examples.');
  }

  const review = analyzeDiff(diff, { source: prUrl || diffFile || 'stdin' });
  if (args.includes('--json')) {
    process.stdout.write(`${JSON.stringify(review, null, 2)}\n`);
  } else {
    process.stdout.write(formatReview(review));
  }
}

main().catch((error) => {
  process.stderr.write(`claude-review: ${error.message}\n`);
  process.exit(1);
});
