const GITHUB_API_BASE = "https://api.github.com";

export function parsePullRequestUrl(prUrl) {
  try {
    const parsed = new URL(prUrl);
    const match = parsed.pathname.match(/^\/([^/]+)\/([^/]+)\/pull\/(\d+)(\/|$)/);

    if (!match) {
      throw new Error("URL does not point to a GitHub pull request");
    }

    return {
      owner: match[1],
      repo: match[2],
      number: Number.parseInt(match[3], 10),
      url: `${parsed.protocol}//${parsed.host}/${match[1]}/${match[2]}/pull/${match[3]}`
    };
  } catch (error) {
    throw new Error(`Invalid pull request URL: ${prUrl}`);
  }
}

function buildHeaders(token, accept = "application/vnd.github+json") {
  const headers = {
    Accept: accept,
    "User-Agent": "claude-review"
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
}

async function fetchJson(url, token) {
  const response = await fetch(url, {
    headers: buildHeaders(token)
  });

  if (!response.ok) {
    throw await createGitHubError(response, url);
  }

  return response.json();
}

async function fetchText(url, token, accept = "text/plain") {
  const response = await fetch(url, {
    headers: buildHeaders(token, accept)
  });

  if (!response.ok) {
    throw await createGitHubError(response, url);
  }

  return response.text();
}

async function createGitHubError(response, url) {
  const body = await response.text();
  const tokenHint = response.status === 403
    ? " GitHub may be rate-limiting unauthenticated requests. Set GITHUB_TOKEN and retry."
    : "";

  return new Error(`GitHub request failed (${response.status}) for ${url}.${tokenHint}\n${body}`);
}

export function clipDiff(diff, limit) {
  if (diff.length <= limit) {
    return {
      diff,
      clipped: false
    };
  }

  return {
    diff: `${diff.slice(0, limit)}\n\n[diff truncated after ${limit} characters]`,
    clipped: true
  };
}

export async function getPullRequestContext(prUrl, options = {}) {
  const token = options.token ?? process.env.GITHUB_TOKEN ?? "";
  const reference = parsePullRequestUrl(prUrl);
  const apiUrl = `${GITHUB_API_BASE}/repos/${reference.owner}/${reference.repo}/pulls/${reference.number}`;
  const diffUrl = `https://patch-diff.githubusercontent.com/raw/${reference.owner}/${reference.repo}/pull/${reference.number}.diff`;

  const [metadata, diff] = await Promise.all([
    fetchJson(apiUrl, token),
    fetchText(diffUrl, token, "text/x-diff")
  ]);

  return {
    author: metadata.user?.login ?? "unknown",
    additions: metadata.additions ?? 0,
    baseRef: metadata.base?.ref ?? "unknown",
    body: metadata.body ?? "",
    changedFiles: metadata.changed_files ?? 0,
    deletions: metadata.deletions ?? 0,
    diff,
    headRef: metadata.head?.ref ?? "unknown",
    number: reference.number,
    owner: reference.owner,
    repo: reference.repo,
    title: metadata.title ?? `PR #${reference.number}`,
    url: reference.url
  };
}
