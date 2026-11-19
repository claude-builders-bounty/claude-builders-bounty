#!/usr/bin/env node
// claude-review — analyze a GitHub PR diff and post a structured Markdown review.
// Usage:
//   node claude-review.cjs --pr <PR-URL>          # stdout review
//   node claude-review.cjs --pr <PR-URL> --post   # post via GH_TOKEN
const { execSync } = require('child_process');

function arg(name, fallback = null) {
  const i = process.argv.indexOf('--' + name);
  return i !== -1 ? (process.argv[i + 1] || 'true') : fallback;
}

const prUrl = arg('pr');
if (!prUrl) {
  console.error('Usage: claude-review --pr https://github.com/owner/repo/pull/123 [--post]');
  process.exit(1);
}
const postMode = typeof arg('post') === 'string' ? arg('post') : arg('post', null) !== null;

const m = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
if (!m) {
  console.error('Error: PR url must look like https://github.com/owner/repo/pull/123');
  process.exit(1);
}
const [, owner, repo, number] = m;

const bucketsOfFile = (name) => {
  const b = [];
  if (/\.sql$|migrat|schema/i.test(name)) b.push('database');
  if (/package\.json|pnpm-lock|yarn.lock|package-lock\.json|^deps\//i.test(name)) b.push('deps');
  if (/auth|login|session|password|token\.(ts|js|go|py)$/i.test(name)) b.push('auth');
  if (/billing|subscription|payment|invoice|stripe|alipay|checkout|order/i.test(name)) b.push('payments');
  if (/(secret|cert|key|\.pem|\.env)$|crypto/i.test(name)) b.push('secrets');
  if (/(\.test\.|__tests__|spec)/i.test(name)) b.push('tests');
  if (/(rm -rf|force push|DROP TABLE|TRUNCATE|DELETE FROM|chmod -R)/i.test(name)) b.push('destructive');
  return b;
};

async function fetchDiff(o, r, n) {
  const api = `https://api.github.com/repos/${o}/${r}/pulls/${n}`;
  const headers = { Accept: 'application/vnd.github.diff', 'User-Agent': 'claude-review' };
  if (process.env.GH_TOKEN) headers.Authorization = 'Bearer ' + process.env.GH_TOKEN;
  const res = await fetch(api, { headers });
  if (!res.ok) {
    if (res.status === 403 || res.status === 429) { console.error(`Error: GitHub rate-limited (${res.status}). Set GH_TOKEN to raise the limit.`); process.exit(1); }
    console.error(`Error: GitHub returned ${res.status}`); process.exit(1);
  }
  return res.text();
}

async function fetchMeta(o, r, n) {
  const api = `https://api.github.com/repos/${o}/${r}/pulls/${n}`;
  const headers = { Accept: 'application/vnd.github+json', 'User-Agent': 'claude-review' };
  if (process.env.GH_TOKEN) headers.Authorization = 'Bearer ' + process.env.GH_TOKEN;
  const res = await fetch(api, { headers });
  if (!res.ok) return null;
  return res.json();
}

function analyze(diff) {
  const files = [];
  const filePattern = /^diff --git a\/(\S+) b\/(\S+)/gm;
  let m;
  while ((m = filePattern.exec(diff))) files.push(m[1]);
  const added = (diff.match(/^[+][^+]/gm) || []).length;
  const removed = (diff.match(/^[-][^-]/gm) || []).length;
  const deletes = (diff.match(/^[-]/gm) || []).length;

  // Find per-bucket counts via file path match
  const bucketFiles = {};
  for (const f of files) {
    for (const b of bucketsOfFile(f)) {
      bucketFiles[b] = (bucketFiles[b] || 0) + 1;
    }
  }
  const buckets = Object.keys(bucketFiles);

  const risks = [];
  const suggestions = [];
  if (bucketFiles.database) risks.push(`Schema/migration changes in ${bucketFiles.database} file(s) — verify rollback and backfill`);
  if (bucketFiles.auth) risks.push(`Authentication paths touched (${bucketFiles.auth} file(s)) — re-check session/CSRF/token handling`);
  if (bucketFiles.payments) risks.push(`Billing paths touched (${bucketFiles.payments} file(s)) — check idempotency + webhook signature validation`);
  if (bucketFiles.deps) risks.push(`Dependency changes in ${bucketFiles.deps} manifest file(s) — pin versions and re-audit`);
  if (bucketFiles.secrets) risks.push(` secrets present (${bucketFiles.secrets} file(s)) — confirm they are example/test values, not live keys`);
  if (bucketFiles.destructive) risks.push(' destructive edit(s) detected — require maintainer sign-off before merge');
  if (files.length > 40) risks.push('Large diff (>40 files) — recommend split into smaller slices');
  if (!buckets.includes('tests') && added > 50) suggestions.push('No test files changed — add coverage for changed code paths');
  if (files.length === 0) suggestions.push('Empty diff — nothing to review');
  if (deletes > added * 2 && files.length > 1) suggestions.push('Mostly deletions — verify nothing was removed unintentionally');
  if (!risks.length) risks.push('No high-risk buckets detected — still review for logic bugs');

  let confidence = 'Medium';
  if (files.length === 0 || added > 2000) confidence = 'Low';
  else if (risks.length <= 1 && files.length <= 10) confidence = 'High';

  return { added, removed, files: files.length, buckets, risks, suggestions, confidence };
}

function markdown(repo, number, meta, a) {
  const title = meta?.title || '(unknown title)';
  const scope = `${a.added} additions, ${a.removed} deletions across ${a.files} files`;
  const lines = [
    '## Review',
    '',
    `**Summary:** PR \`${repo}#${number} — ${title}\` changes ${scope}. Domains: ${a.buckets.join(', ') || 'general'}.`,
    '',
    '**Risks**',
    ...a.risks.map(r => '- ' + r),
    '',
    '**Suggestions**',
    ...a.suggestions.map(s => '- ' + s),
    '',
    '**Confidence:** ' + a.confidence,
    '',
    '_Generated by `claude-review` (heuristic, not a replacement for manual review)._',
  ];
  return lines.join('\n');
}

(async () => {
  let diff, meta = null;
  try {
    [diff, meta] = await Promise.all([fetchDiff(owner, repo, number), fetchMeta(owner, repo, number)]);
  } catch (e) {
    console.error('Error analyzing PR: ' + e.message);
    process.exit(1);
  }
  const a = analyze(diff);
  const md = markdown(owner + '/' + repo, number, meta, a);
  if (postMode) {
    if (!process.env.GH_TOKEN) { console.error('GH_TOKEN required for --post'); process.exit(1); }
    const res = await fetch('https://api.github.com/repos/' + owner + '/' + repo + '/issues/' + number + '/comments', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + process.env.GH_TOKEN, 'User-Agent': 'claude-review', Accept: 'application/vnd.github+json', 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ body: md }),
    });
    if (!res.ok) { console.error('GitHub returned ' + res.status); process.exit(1); }
    const comment = await res.json();
    console.log('Posted: ' + comment.html_url);
    return;
  }
  process.stdout.write(md + '\n');
})();
