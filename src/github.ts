import { DiffResult, PRInfo } from "./types";

interface GitHubAPIResponse {
  number: number;
  title: string;
  user: { login: string } | null;
  html_url: string;
  base: {
    repo: { full_name: string };
    ref: string;
  };
  head: {
    repo: { full_name: string };
    ref: string;
  };
  additions?: number;
  deletions?: number;
  changed_files?: number;
}

function parseGitHubUrl(url: string): { owner: string; repo: string; prNumber: number } | null {
  const match = url.match(
    /https?:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/
  );
  if (!match) return null;
  return {
    owner: match[1],
    repo: match[2],
    prNumber: parseInt(match[3], 10),
  };
}

function getHeaders(): Record<string, string> {
  const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;
  const headers: Record<string, string> = {
    Accept: "application/vnd.github.v3+json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { headers: getHeaders() });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(
      `GitHub API error ${response.status}: ${response.statusText}${body ? ` — ${body}` : ""}`
    );
  }
  return (await response.json()) as T;
}

async function fetchText(url: string): Promise<string> {
  const response = await fetch(url, {
    headers: {
      Accept: "application/vnd.github.v3.diff",
      ...getHeaders(),
    },
  });
  if (!response.ok) {
    throw new Error(
      `GitHub API error ${response.status}: ${response.statusText}`
    );
  }
  return response.text();
}

export async function fetchPRDiff(prUrl: string): Promise<DiffResult> {
  const parsed = parseGitHubUrl(prUrl);
  if (!parsed) {
    throw new Error(
      `Invalid GitHub PR URL. Expected format: https://github.com/owner/repo/pull/123\nGot: ${prUrl}`
    );
  }

  const { owner, repo, prNumber } = parsed;

  // Fetch PR metadata
  const prApiUrl = `https://api.github.com/repos/${owner}/${repo}/pulls/${prNumber}`;
  const prData = await fetchJson<GitHubAPIResponse>(prApiUrl);

  const prInfo: PRInfo = {
    number: prData.number,
    title: prData.title,
    author: prData.user?.login ?? "unknown",
    htmlUrl: prData.html_url,
    baseRepo: prData.base.repo.full_name,
    baseBranch: prData.base.ref,
    headRepo: prData.head.repo.full_name,
    headBranch: prData.head.ref,
    additions: prData.additions ?? 0,
    deletions: prData.deletions ?? 0,
    changedFiles: prData.changed_files ?? 0,
  };

  // Fetch diff
  const diffText = await fetchText(prApiUrl);

  const diffSizeKB = Math.round(
    (new TextEncoder().encode(diffText).length / 1024) * 100
  ) / 100;

  return { prInfo, diff: diffText, diffSizeKB };
}

export async function postPRComment(
  prUrl: string,
  comment: string
): Promise<void> {
  const parsed = parseGitHubUrl(prUrl);
  if (!parsed) {
    throw new Error(`Invalid GitHub PR URL: ${prUrl}`);
  }

  const { owner, repo, prNumber } = parsed;
  const commentApiUrl = `https://api.github.com/repos/${owner}/${repo}/issues/${prNumber}/comments`;

  const response = await fetch(commentApiUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getHeaders(),
    },
    body: JSON.stringify({ body: comment }),
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(
      `Failed to post comment (${response.status}): ${response.statusText}${body ? ` — ${body}` : ""}`
    );
  }

  console.log(`✅ Comment posted to PR #${prNumber}`);
}
