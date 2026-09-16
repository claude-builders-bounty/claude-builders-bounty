const GITHUB_PR_RE = /^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)(?:[/?#].*)?$/;

export async function fetchPullRequest(prUrl) {
  const match = prUrl.match(GITHUB_PR_RE);
  if (!match) {
    throw new Error("Expected a public GitHub pull request URL.");
  }

  const [, owner, repo, pullNumber] = match;
  const base = `https://api.github.com/repos/${owner}/${repo}`;
  const headers = {
    "accept": "application/vnd.github+json",
    "user-agent": "AtlasPRReviewAgent/0.1 read-only",
  };

  const [pull, files] = await Promise.all([
    getJson(`${base}/pulls/${pullNumber}`, headers),
    getJson(`${base}/pulls/${pullNumber}/files?per_page=100`, headers),
  ]);

  return {
    url: prUrl,
    owner,
    repo,
    number: Number(pullNumber),
    title: pull.title || "",
    body: pull.body || "",
    state: pull.state || "",
    author: pull.user?.login || "",
    base: pull.base?.ref || "",
    head: pull.head?.ref || "",
    additions: pull.additions || 0,
    deletions: pull.deletions || 0,
    changedFiles: pull.changed_files || files.length,
    files: files.map((file) => ({
      filename: file.filename,
      status: file.status,
      additions: file.additions || 0,
      deletions: file.deletions || 0,
      changes: file.changes || 0,
      patch: file.patch || "",
    })),
  };
}

async function getJson(url, headers) {
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`GitHub API ${response.status} for ${url}`);
  }
  return response.json();
}

