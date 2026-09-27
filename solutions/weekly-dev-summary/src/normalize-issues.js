const settings = $('Build Settings').first().json;
const start = Date.parse(settings.since);
const end = Date.parse(settings.until);
if (!coverage.complete) throw new Error('Issue pagination did not reach its last page');

const seen = new Set();
const items = rows.filter((row) => {
  if (!row || seen.has(row.number) || row.pull_request || row.state !== 'closed' || !row.closed_at) return false;
  const closed = Date.parse(row.closed_at);
  if (!Number.isFinite(closed) || closed < start || closed > end) return false;
  seen.add(row.number);
  return true;
}).map((row) => ({
  number: row.number,
  title: String(row.title || '').slice(0, 180),
  closedAt: row.closed_at,
  url: row.html_url,
}));

return [{ json: { kind: 'issues', items, coverage } }];
