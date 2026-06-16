#!/usr/bin/env node
/**
 * Integration test: GitHub API fetch logic used by the workflow.
 * Uses GITHUB_TOKEN, or falls back to `gh auth token` when available.
 * Optional GITHUB_REPO (default: claude-builders-bounty/claude-builders-bounty).
 */
import { execSync } from 'node:child_process';
import { fetchGitHubPages, validateGitHubToken } from './lib/github-collect.mjs';

const repo = process.env.GITHUB_REPO || 'claude-builders-bounty/claude-builders-bounty';

function resolveToken() {
  if (process.env.GITHUB_TOKEN) return process.env.GITHUB_TOKEN;
  try {
    return execSync('gh auth token', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return '';
  }
}

const token = resolveToken();
const [owner, name] = repo.split('/');

if (!token) {
  console.error('FAIL: GITHUB_TOKEN not set and gh CLI is not authenticated');
  process.exit(1);
}

await validateGitHubToken(token);

const weekStart = new Date();
weekStart.setDate(weekStart.getDate() - 7);

const commits = await fetchGitHubPages(
  `https://api.github.com/repos/${owner}/${name}/commits`,
  token,
  { since: weekStart.toISOString() },
);
const issues = await fetchGitHubPages(
  `https://api.github.com/repos/${owner}/${name}/issues`,
  token,
  { state: 'closed', since: weekStart.toISOString() },
);
const search = await fetchGitHubPages(
  'https://api.github.com/search/issues',
  token,
  {
    q: `repo:${repo} is:pr is:merged merged:>=${weekStart.toISOString().slice(0, 10)}`,
    sort: 'updated',
  },
);

const closedIssues = issues.filter((i) => !i.pull_request);
const mergedPrs = search;

console.log(`OK: ${repo} — ${commits.length} commits, ${closedIssues.length} closed issues, ${mergedPrs.length} merged PRs (7d window, paginated)`);
