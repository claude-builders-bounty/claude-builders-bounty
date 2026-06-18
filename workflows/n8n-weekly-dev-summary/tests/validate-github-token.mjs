#!/usr/bin/env node
/**
 * Pre-flight check: verify GITHUB_TOKEN can read GITHUB_REPO before running the workflow.
 * Sends GET https://api.github.com/repos/{owner}/{repo} and fails on 401/403/404.
 *
 * Usage:
 *   GITHUB_TOKEN=<your-token> GITHUB_REPO=owner/repo node tests/validate-github-token.mjs
 *   npm run test:validate-token
 */
import { execSync } from 'node:child_process';
import { validateGitHubToken } from './lib/github-collect.mjs';

function resolveToken() {
  if (process.env.GITHUB_TOKEN) return process.env.GITHUB_TOKEN.trim();
  try {
    return execSync('gh auth token', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return '';
  }
}

const repo = (process.env.GITHUB_REPO || 'claude-builders-bounty/claude-builders-bounty').trim();
const token = resolveToken();

if (!token) {
  console.error('FAIL: Set GITHUB_TOKEN (or authenticate gh CLI) before validating repo access.');
  process.exit(1);
}

if (!/^[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+$/.test(repo)) {
  console.error('FAIL: Set GITHUB_REPO to owner/repo with GitHub-safe characters only.');
  process.exit(1);
}

try {
  const repoName = await validateGitHubToken(token, { repo });
  console.log(`OK: GITHUB_TOKEN can read ${repoName} (repo read access verified)`);
} catch (error) {
  console.error(`FAIL: ${error.message}`);
  process.exit(1);
}
