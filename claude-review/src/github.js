'use strict';

function parsePrUrl(url) {
  const match = url.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) {
    throw new Error(`Invalid GitHub PR URL: ${url}`);
  }
  return { owner: match[1], repo: match[2], number: parseInt(match[3], 10) };
}

async function fetchPrData(owner, repo, number, token) {
  const headers = {
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'claude-review',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const baseUrl = `https://api.github.com/repos/${owner}/${repo}/pulls/${number}`;

  const prResponse = await fetch(baseUrl, { headers });
  if (!prResponse.ok) {
    throw new Error(`Failed to fetch PR: ${prResponse.status} ${prResponse.statusText}`);
  }
  const prData = await prResponse.json();

  const diffResponse = await fetch(baseUrl, {
    headers: { ...headers, 'Accept': 'application/vnd.github.v3.diff' },
  });
  if (!diffResponse.ok) {
    throw new Error(`Failed to fetch diff: ${diffResponse.status} ${diffResponse.statusText}`);
  }
  const diff = await diffResponse.text();

  return {
    title: prData.title,
    body: prData.body || '',
    author: prData.user.login,
    base: prData.base.ref,
    head: prData.head.ref,
    filesChanged: prData.changed_files,
    additions: prData.additions,
    deletions: prData.deletions,
    diff,
  };
}

async function postComment(owner, repo, number, body, token) {
  if (!token) {
    throw new Error('GitHub token is required to post comments');
  }

  const url = `https://api.github.com/repos/${owner}/${repo}/issues/${number}/comments`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'application/vnd.github.v3+json',
      'Authorization': `Bearer ${token}`,
      'User-Agent': 'claude-review',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ body }),
  });

  if (!response.ok) {
    throw new Error(`Failed to post comment: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

module.exports = { parsePrUrl, fetchPrData, postComment };
