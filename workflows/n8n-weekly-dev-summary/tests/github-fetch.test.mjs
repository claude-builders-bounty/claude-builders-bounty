#!/usr/bin/env node
/**
 * Integration test: GitHub API fetch logic used by the workflow.
 * CI sets UPSTREAM_STATUS_TOKEN (dedicated PAT); local runs may use GITHUB_TOKEN or gh auth.
 * Optional GITHUB_REPO (default: claude-builders-bounty/claude-builders-bounty).
 */
import { fetchGitHubPages, validateGitHubToken } from './lib/github-collect.mjs';
import { describeGitHubTestTokenSource, resolveGitHubTestToken } from './lib/github-test-token.mjs';

const repo = process.env.GITHUB_REPO || 'claude-builders-bounty/claude-builders-bounty';
const token = resolveGitHubTestToken();
const [owner, name] = repo.split('/');

if (!token) {
  console.error('FAIL: GitHub token required for test:github');
  console.error('Set UPSTREAM_STATUS_TOKEN=<token>, GITHUB_TOKEN=<token>, or authenticate the gh CLI.');
  process.exit(1);
}

const source = describeGitHubTestTokenSource();
if (source !== 'UPSTREAM_STATUS_TOKEN') {
  console.warn(`WARN: using ${source} fallback for local GitHub integration test`);
}

await validateGitHubToken(token, { repo });

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
