const settings = $('Build Settings').first().json;
const start = Date.parse(settings.since);
const end = Date.parse(settings.until);
if (!coverage.complete) throw new Error('Commit pagination did not reach its last page');

const seen = new Set();
const items = rows.filter((row) => {
  const date = Date.parse(row?.commit?.committer?.date || row?.commit?.author?.date);
  if (!row?.sha || seen.has(row.sha) || !Number.isFinite(date) || date < start || date > end) return false;
  seen.add(row.sha);
  return true;
})
  .map((row) => ({
    sha: String(row.sha).slice(0, 12),
    date: row.commit.committer?.date || row.commit.author.date,
    author: row.author?.login || row.commit.author.name || 'unknown',
    title: String(row.commit.message || '').split('\n')[0].slice(0, 180),
    url: row.html_url,
  }));

return [{ json: { kind: 'commits', items, coverage } }];
