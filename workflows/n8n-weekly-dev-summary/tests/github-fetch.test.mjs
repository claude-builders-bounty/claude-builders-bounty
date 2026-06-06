#!/usr/bin/env node
/**
 * Integration test: GitHub API fetch logic used by the workflow.
 * Requires GITHUB_TOKEN (optional GITHUB_REPO).
 */
const repo = process.env.GITHUB_REPO || 'claude-builders-bounty/claude-builders-bounty';
const token = process.env.GITHUB_TOKEN;
const [owner, name] = repo.split('/');

if (!token) {
  console.error('SKIP: GITHUB_TOKEN not set');
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
