import { config } from "./config.js";

const GH_API = "https://api.github.com";

function headers(extra = {}) {
  return {
    Authorization: `Bearer ${config.githubToken}`,
    Accept: "application/vnd.github.v3+json",
    "Content-Type": "application/json",
    ...extra,
  };
}

export async function fetchPrInfo(owner, repo, prNumber) {
  const res = await fetch(
    `${GH_API}/repos/${owner}/${repo}/pulls/${prNumber}`,
    { headers }
  );
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GitHub API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function fetchPrDiff(owner, repo, prNumber) {
  const res = await fetch(
    `${GH_API}/repos/${owner}/${repo}/pulls/${prNumber}`,
    { headers: { ...headers(), Accept: "application/vnd.github.v3.diff" } }
  );
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GitHub API error ${res.status}: ${text}`);
  }
  return res.text();
}

export async function fetchPrComments(owner, repo, prNumber) {
  const res = await fetch(
    `${GH_API}/repos/${owner}/${repo}/pulls/${prNumber}/comments`,
    { headers }
  );
  if (!res.ok) return [];
  return res.json();
}

export async function fetchFiles(owner, repo, prNumber) {
  const res = await fetch(
    `${GH_API}/repos/${owner}/${repo}/pulls/${prNumber}/files`,
    { headers }
  );
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GitHub API error ${res.status}: ${text}`);
  }
  return res.json();
}

export function parsePrUrl(url) {
  const match = url.match(
    /github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/
  );
  if (!match) {
    throw new Error(
      "Invalid PR URL. Expected format: https://github.com/owner/repo/pull/123"
    );
  }
  return { owner: match[1], repo: match[2], prNumber: parseInt(match[3], 10) };
}
