const settings = $('Build Settings').first().json;
const start = Date.parse(settings.since);
const end = Date.parse(settings.until);
// The endpoint is ordered by updated_at descending. No older page can contain
// a PR merged this week once this page reaches an earlier update timestamp.
const reachedOlderUpdates = lastPage.body.some((row) => Date.parse(row.updated_at) < start);
coverage.complete ||= reachedOlderUpdates;
if (!coverage.complete) throw new Error('Pull request pagination did not cover the weekly window');

const seen = new Set();
const items = rows.filter((row) => {
  if (!row?.merged_at || seen.has(row.number)) return false;
  const merged = Date.parse(row.merged_at);
  if (!Number.isFinite(merged) || merged < start || merged > end) return false;
  seen.add(row.number);
  return true;
}).map((row) => ({
  number: row.number,
  title: String(row.title || '').slice(0, 180),
  mergedAt: row.merged_at,
  url: row.html_url,
}));

return [{ json: { kind: 'pulls', items, coverage } }];
