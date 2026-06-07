#!/usr/bin/env node
/**
 * Integration test: GitHub API fetch logic used by the workflow.
 * Uses GITHUB_TOKEN, or falls back to `gh auth token` when available.
 * Optional GITHUB_REPO (default: claude-builders-bounty/claude-builders-bounty).
 */
import { execSync } from 'node:child_process';

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
  console.error('SKIP: GITHUB_TOKEN not set and gh CLI is not authenticated');
  process.exit(0);
}

const weekStart = new Date();
weekStart.setDate(weekStart.getDate() - 7);

async function gh(path, params = {}) {
  const url = new URL(`https://api.github.com${path}`);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
    },
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

const commits = await gh(`/repos/${owner}/${name}/commits`, {
  since: weekStart.toISOString(),
  per_page: '100',
});
const issues = await gh(`/repos/${owner}/${name}/issues`, {
  state: 'closed',
  since: weekStart.toISOString(),
  per_page: '100',
});
const search = await gh('/search/issues', {
  q: `repo:${repo} is:pr is:merged merged:>=${weekStart.toISOString().slice(0, 10)}`,
  per_page: '100',
  sort: 'updated',
});

const closedIssues = issues.filter((i) => !i.pull_request);
const mergedPrs = search.items || [];

console.log(`OK: ${repo} — ${commits.length} commits, ${closedIssues.length} closed issues, ${mergedPrs.length} merged PRs (7d window)`);
