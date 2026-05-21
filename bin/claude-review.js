#!/usr/bin/env node
const { execFileSync } = require('node:child_process');

function help() {
  console.log(`Usage: claude-review --pr https://github.com/owner/repo/pull/123 [--dry-run]\n\nEnv:\n  ANTHROPIC_API_KEY  Optional. If set, uses Claude for review.\n  GITHUB_TOKEN       Optional. Improves GitHub API rate limits.`);
}

function arg(name) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

function parsePr(url) {
  const m = String(url || '').match(/^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!m) throw new Error('Expected --pr https://github.com/owner/repo/pull/123');
  return { owner: m[1], repo: m[2], number: m[3] };
}

function gh(args) {
  return execFileSync('gh', args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}

function fallbackReview(pr, meta, diff) {
  const files = [...diff.matchAll(/^diff --git a\/(.*?) b\/(.*?)$/gm)].map(m => m[2]);
  const added = (diff.match(/^\+/gm) || []).length;
  const removed = (diff.match(/^-/gm) || []).length;
  return `## Summary\nThis PR updates ${files.length || 'the'} file(s) in ${pr.owner}/${pr.repo}. The diff contains about ${added} added and ${removed} removed lines, so this review focuses on change shape and obvious risk areas.\n\n## Identified risks\n- Automated fallback review was used because ANTHROPIC_API_KEY was not set.\n- Large or cross-cutting files may need domain-specific manual review.\n- Test impact cannot be fully confirmed from the diff alone.\n\n## Improvement suggestions\n- Verify the changed paths have matching tests or documented manual validation.\n- Check error handling and edge cases around any modified public API or workflow.\n- Run the repo's normal formatter, linter, and test suite before merge.\n\n## Confidence score\nLow\n`;
}

async function claudeReview(pr, meta, diff) {
  if (!process.env.ANTHROPIC_API_KEY) return fallbackReview(pr, meta, diff);
  const prompt = `Review this GitHub PR diff. Return Markdown with exactly these sections: Summary of changes (2-3 sentences), Identified risks (list), Improvement suggestions (list), Confidence score: Low / Medium / High.\n\nPR: ${JSON.stringify(meta)}\n\nDIFF:\n${diff.slice(0, 120000)}`;
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': process.env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({ model: 'claude-3-5-sonnet-latest', max_tokens: 1200, messages: [{ role: 'user', content: prompt }] })
  });
  if (!res.ok) throw new Error(`Claude API failed: ${res.status} ${await res.text()}`);
  const json = await res.json();
  return json.content.map(c => c.text || '').join('\n').trim();
}

async function main() {
  if (process.argv.includes('--help') || process.argv.length === 2) return help();
  const prUrl = arg('--pr');
  const pr = parsePr(prUrl);
  let meta = {};
  let diff = '';
  if (process.argv.includes('--dry-run')) {
    meta = { title: 'Dry run PR', url: prUrl };
    diff = 'diff --git a/README.md b/README.md\n+Example change\n';
  } else {
    meta = JSON.parse(gh(['api', `repos/${pr.owner}/${pr.repo}/pulls/${pr.number}`]));
    diff = gh(['pr', 'diff', prUrl]);
  }
  console.log(await claudeReview(pr, meta, diff));
}

main().catch(err => { console.error(err.message); process.exit(1); });
