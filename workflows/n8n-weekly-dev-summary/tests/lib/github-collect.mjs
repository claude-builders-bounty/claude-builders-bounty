/**
 * Shared GitHub collection helpers mirrored by n8n workflow Code nodes.
 * Tests import this module so regressions catch logic drift in weekly-dev-summary.json.
 */

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
  const rows = items.map((item) => item?.json?.records ?? item?.json).filter(Boolean);
  if (rows.length === 1 && Array.isArray(rows[0])) return rows[0].filter((row) => !isGitHubError(row));
  if (rows.length === 1 && Array.isArray(rows[0]?.records)) {
    return rows[0].records.filter((row) => !isGitHubError(row));
  }
  const flat = rows.flatMap((row) => (Array.isArray(row?.records) ? row.records : [row]));
  return flat.filter((row) => row && typeof row === 'object' && !Array.isArray(row) && !isGitHubError(row));
}

export async function fetchGitHubPages(baseUrl, token, query = {}, { maxPages = 50 } = {}) {
  const headers = {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
  };
  const records = [];
  let page = 1;

  while (page <= maxPages) {
    const params = new URLSearchParams({ ...query, per_page: '100', page: String(page) });
    const res = await fetch(`${baseUrl}?${params}`, { headers });
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
