const API_ROOT = "https://api.github.com";

function parsePullRequestUrl(input) {
  let url;
  try {
    url = new URL(input);
  } catch {
    throw new Error(`Invalid PR URL: ${input}`);
  }

  if (url.hostname !== "github.com") {
    throw new Error("Only github.com pull request URLs are supported");
  }

  const match = url.pathname.match(/^\/([^/]+)\/([^/]+)\/pull\/(\d+)\/?$/);
  if (!match) {
    throw new Error("Expected a URL like https://github.com/owner/repo/pull/123");
  }

  return {
    owner: match[1],
    repo: match[2],
    number: Number(match[3]),
    htmlUrl: `https://github.com/${match[1]}/${match[2]}/pull/${match[3]}`,
  };
}

function headers(token, accept = "application/vnd.github+json") {
  const base = {
    Accept: accept,
    "User-Agent": "claude-pr-review-agent",
    "X-GitHub-Api-Version": "2022-11-28",
  };
  if (token) {
    base.Authorization = `Bearer ${token}`;
  }
  return base;
}

async function githubJson(url, token) {
  const response = await fetch(url, { headers: headers(token) });
  if (!response.ok) {
    throw new Error(`GitHub API request failed ${response.status}: ${url}`);
  }
  return response.json();
}

async function githubText(url, token, accept) {
  const response = await fetch(url, { headers: headers(token, accept) });
  if (!response.ok) {
    throw new Error(`GitHub request failed ${response.status}: ${url}`);
  }
  return response.text();
}

function parseDiffFiles(diff) {
  const files = [];
  let current = null;

  for (const line of diff.split("\n")) {
    const fileMatch = line.match(/^diff --git a\/(.+) b\/(.+)$/);
    if (fileMatch) {
      current = {
        filename: fileMatch[2],
        status: "modified",
        additions: 0,
        deletions: 0,
        changes: 0,
      };
      files.push(current);
      continue;
    }

    if (!current) {
      continue;
    }

    if (line.startsWith("new file mode")) {
      current.status = "added";
    } else if (line.startsWith("deleted file mode")) {
      current.status = "removed";
    } else if (line.startsWith("+") && !line.startsWith("+++")) {
      current.additions += 1;
      current.changes += 1;
    } else if (line.startsWith("-") && !line.startsWith("---")) {
      current.deletions += 1;
      current.changes += 1;
    }
  }

  return files;
}

async function fetchDiff(identity, token) {
  const base = `${API_ROOT}/repos/${identity.owner}/${identity.repo}`;
  try {
    return await githubText(
      `${base}/pulls/${identity.number}`,
      token,
      "application/vnd.github.v3.diff",
    );
  } catch (apiError) {
    return githubText(
      `${identity.htmlUrl}.diff`,
      token,
      "text/plain",
    );
  }
}

async function fetchPullRequest(input, { token = "" } = {}) {
  const identity = parsePullRequestUrl(input);
  const base = `${API_ROOT}/repos/${identity.owner}/${identity.repo}`;
  const diff = await fetchDiff(identity, token);
  const parsedFiles = parseDiffFiles(diff);

  let pull = {};
  let files = parsedFiles;
  try {
    [pull, files] = await Promise.all([
      githubJson(`${base}/pulls/${identity.number}`, token),
      githubJson(`${base}/pulls/${identity.number}/files?per_page=100`, token),
    ]);
  } catch {
    pull = {};
    files = parsedFiles;
  }

  const additions =
    pull.additions ?? files.reduce((sum, file) => sum + file.additions, 0);
  const deletions =
    pull.deletions ?? files.reduce((sum, file) => sum + file.deletions, 0);

  return {
    ...identity,
    title: pull.title || "",
    body: pull.body || "",
    author: pull.user?.login || "unknown",
    baseRef: pull.base?.ref || "",
    headRef: pull.head?.ref || "",
    changedFiles: pull.changed_files || files.length,
    additions,
    deletions,
    files: files.map((file) => ({
      filename: file.filename,
      status: file.status,
      additions: file.additions,
      deletions: file.deletions,
      changes: file.changes,
    })),
    diff,
  };
}

module.exports = {
  fetchPullRequest,
  parseDiffFiles,
  parsePullRequestUrl,
};
