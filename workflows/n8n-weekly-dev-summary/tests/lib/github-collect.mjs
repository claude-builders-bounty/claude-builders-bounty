/**
 * Shared GitHub collection helpers mirrored by n8n workflow Code nodes.
 * Tests import this module so regressions catch logic drift in weekly-dev-summary.json.
 */

export const GITHUB_USER_URL = 'https://api.github.com/user';

export function githubRepoUrl(repoFull) {
  const [owner, repo] = String(repoFull || '').split('/');
  return `https://api.github.com/repos/${owner}/${repo}`;
}

export function githubAuthHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
  };
}

/**
 * Verify GITHUB_TOKEN can read the target repo (or /user when no repo is given).
 * Repo-scoped validation works with GitHub Actions GITHUB_TOKEN (contents: read).
 * @param {string} token - GitHub PAT or OAuth token
 * @param {{ fetchFn?: typeof fetch, repo?: string } | typeof fetch} [options]
 * @returns {Promise<string>} repo full_name or authenticated GitHub login
 */
export async function validateGitHubToken(token, options = {}) {
  const normalized =
    typeof options === 'function' ? { fetchFn: options } : options;
  const { fetchFn = fetch, repo: repoFull = null } = normalized;

  const trimmed = (token || '').trim();
  if (!trimmed) {
    throw new Error('Set GITHUB_TOKEN with repo read access.');
  }

  const url = repoFull ? githubRepoUrl(repoFull) : GITHUB_USER_URL;
  const res = await fetchFn(url, { headers: githubAuthHeaders(trimmed) });
  const body = await res.json().catch(() => ({}));

  if (res.status === 401 || res.status === 403) {
    throw new Error('GITHUB_TOKEN is invalid or lacks required permissions.');
  }
  if (!res.ok) {
    throw new Error(
      `GitHub token validation failed: ${res.status} ${body.message || res.statusText || ''}`.trim(),
    );
  }
  if (repoFull) {
    if (!body || typeof body.full_name !== 'string') {
      throw new Error('GITHUB_TOKEN validation failed: unexpected GitHub response.');
    }
    return body.full_name;
  }
  if (!body || typeof body.login !== 'string') {
    throw new Error('GITHUB_TOKEN validation failed: unexpected GitHub response.');
  }

  return body.login;
}

export function isGitHubError(row) {
  return Boolean(
    row &&
      typeof row === 'object' &&
      !Array.isArray(row) &&
      typeof row.message === 'string' &&
      typeof row.documentation_url === 'string',
  );
}

export function collectRecords(items) {
  if (!Array.isArray(items) || !items.length) return [];

  const rows = items.flatMap((item) => {
    const json = item?.json;
    if (!json) return [];
    if (Array.isArray(json.records)) return json.records;
    if (Array.isArray(json)) return json;
    return [json];
  });

  return rows.filter(
    (row) => row && typeof row === 'object' && !Array.isArray(row) && !isGitHubError(row),
  );
}

export async function fetchGitHubPages(baseUrl, token, query = {}, { maxPages = 50, fetchFn = fetch } = {}) {
  const headers = githubAuthHeaders((token || '').trim());
  const records = [];
  let page = 1;

  while (page <= maxPages) {
    const params = new URLSearchParams({ ...query, per_page: '100', page: String(page) });
    const res = await fetchFn(`${baseUrl}?${params}`, { headers });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(`GitHub ${baseUrl} failed: ${res.status} ${body.message || res.statusText || ''}`.trim());
    }
    if (isGitHubError(body)) {
      throw new Error(body.message);
    }

    let batch = [];
    if (Array.isArray(body)) {
      batch = body;
    } else if (Array.isArray(body.items)) {
      batch = body.items;
    } else {
      break;
    }

    records.push(...batch.filter((row) => !isGitHubError(row)));
    if (batch.length < 100) break;
    page += 1;
  }

  return records;
}
