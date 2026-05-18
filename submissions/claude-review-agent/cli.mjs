#!/usr/bin/env node
// Claude Code PR Review Agent
// Usage: node cli.mjs --pr https://github.com/owner/repo/pull/123
// Usage: node cli.mjs --diff path/to/diff.txt
// Usage: node cli.mjs --stdin (reads diff from stdin)

import { reviewPR } from './review.mjs';
import { readFileSync } from 'fs';

const args = process.argv.slice(2);

async function main() {
  let diff = '';
  let prUrl = '';

  // Parse args
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--pr' && args[i + 1]) {
      prUrl = args[i + 1];
      i++;
    } else if (args[i] === '--diff' && args[i + 1]) {
      diff = readFileSync(args[i + 1], 'utf-8');
      i++;
    } else if (args[i] === '--stdin') {
      // Read from stdin
      const chunks = [];
      for await (const chunk of process.stdin) {
        chunks.push(chunk);
      }
      diff = Buffer.concat(chunks).toString('utf-8');
    } else if (args[i] === '--help' || args[i] === '-h') {
      console.log(`Claude Code PR Review Agent

Usage:
  node cli.mjs --pr <pr_url>          Fetch PR diff from GitHub and review
  node cli.mjs --diff <file>          Review a local diff file
  node cli.mjs --stdin < diff.txt     Read diff from stdin
  node cli.mjs --help                 Show this help

Environment:
  GITHUB_TOKEN     GitHub personal access token (for API access)
  ANTHROPIC_API_KEY Anthropic API key (for Claude, if using API)
`);
      process.exit(0);
    }
  }

  if (!prUrl && !diff) {
    console.error('Error: --pr <url>, --diff <file>, or --stdin required');
    console.error('Try --help for usage');
    process.exit(1);
  }

  if (prUrl && !diff) {
    diff = await fetchPRDiff(prUrl);
    console.log(`📥 Fetched PR diff from: ${prUrl}\n`);
  }

  if (!diff.trim()) {
    console.error('Error: Empty diff received');
    process.exit(1);
  }

  const result = await reviewPR(diff, prUrl);
  console.log(result);
}

async function fetchPRDiff(prUrl) {
  // Parse owner/repo/pull/number from URL
  const match = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) {
    throw new Error('Invalid GitHub PR URL format. Expected: https://github.com/owner/repo/pull/number');
  }
  
  const [, owner, repo, prNumber] = match;
  const diffUrl = `https://github.com/${owner}/${repo}/pull/${prNumber}.diff`;
  
  const headers = {
    'Accept': 'application/vnd.github.v3.diff',
    'User-Agent': 'claude-review-agent/1.0'
  };
  
  if (process.env.GITHUB_TOKEN) {
    headers['Authorization'] = `token ${process.env.GITHUB_TOKEN}`;
  }

  const response = await fetch(diffUrl, { headers });
  
  if (!response.ok) {
    // Try without .diff extension (private repos may need API)
    if (response.status === 404) {
      const apiUrl = `https://api.github.com/repos/${owner}/${repo}/pulls/${prNumber}`;
      const apiHeaders = {
        'Accept': 'application/vnd.github.v3.diff',
        'User-Agent': 'claude-review-agent/1.0'
      };
      if (process.env.GITHUB_TOKEN) {
        apiHeaders['Authorization'] = `token ${process.env.GITHUB_TOKEN}`;
      }
      const apiResp = await fetch(apiUrl, { headers: apiHeaders });
      if (!apiResp.ok) {
        throw new Error(`Failed to fetch PR diff: HTTP ${apiResp.status}`);
      }
      return await apiResp.text();
    }
    throw new Error(`Failed to fetch PR diff: HTTP ${response.status}`);
  }

  return await response.text();
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
