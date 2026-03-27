/**
 * Fetch PR diff and metadata from GitHub API.
 * Uses native fetch (Node 18+) — zero external deps.
 */

/**
 * Parse a GitHub PR URL into owner, repo, and pull number.
 * @param {string} url - GitHub PR URL
 * @returns {{ owner: string, repo: string, pullNumber: number }}
 */
export function parsePrUrl(url) {
  const match = url.match(
    /github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/
  );
  if (!match) {
    throw new Error(
      `Invalid GitHub PR URL: ${url}\nExpected format: https://github.com/owner/repo/pull/123`
    );
  }
  return {
    owner: match[1],
    repo: match[2],
    pullNumber: parseInt(match[3], 10),
  };
}

/**
 * Fetch the raw diff for a pull request.
 * @param {string} owner
 * @param {string} repo
 * @param {number} pullNumber
 * @param {string} [token] - Optional GitHub token for private repos / higher rate limits
 * @returns {Promise<string>} The unified diff
 */
export async function fetchDiff(owner, repo, pullNumber, token) {
  const url = `https://api.github.com/repos/${owner}/${repo}/pulls/${pullNumber}`;
  const headers = {
    Accept: "application/vnd.github.v3.diff",
    "User-Agent": "claude-review/1.0",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(url, { headers });
  if (!res.ok) {
    throw new Error(
      `GitHub API error ${res.status}: ${res.statusText}\nURL: ${url}`
    );
  }
  return res.text();
}

/**
 * Fetch PR metadata (title, body, changed files, additions, deletions).
 * @param {string} owner
 * @param {string} repo
 * @param {number} pullNumber
 * @param {string} [token]
 * @returns {Promise<Object>}
 */
export async function fetchPrMeta(owner, repo, pullNumber, token) {
  const url = `https://api.github.com/repos/${owner}/${repo}/pulls/${pullNumber}`;
  const headers = {
    Accept: "application/vnd.github.v3+json",
    "User-Agent": "claude-review/1.0",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(url, { headers });
  if (!res.ok) {
    throw new Error(
      `GitHub API error ${res.status}: ${res.statusText}\nURL: ${url}`
    );
  }
  const data = await res.json();
  return {
    title: data.title,
    body: data.body || "(no description)",
    changedFiles: data.changed_files,
    additions: data.additions,
    deletions: data.deletions,
    author: data.user?.login || "unknown",
    base: data.base?.ref || "main",
    head: data.head?.ref || "unknown",
  };
}
