#!/usr/bin/env node
/**
 * claude-review — fetch a PR diff via GitHub API, call Claude Sonnet 4,
 * and emit structured Markdown: Summary / Risks / Suggestions / Confidence.
 *
 * Usage:
 *   claude-review --pr https://github.com/owner/repo/pull/123 [--output review.md] [--comment]
 *   ANTHROPIC_API_KEY=sk-ant-... claude-review --pr https://...
 *   GITHUB_TOKEN=ghp_... claude-review --pr https://...   (higher rate limit + optional --comment)
 */

const MODEL = 'claude-sonnet-4-20250514';
const MAX_DIFF_CHARS = 120_000;
const MAX_FILE_PATCH = 20_000;

// ── arg parsing ────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const args = { pr: null, output: null, comment: false, help: false, json: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--pr' || a === '--pull-request') args.pr = argv[++i];
    else if (a === '--output' || a === '-o') args.output = argv[++i];
    else if (a === '--comment') args.comment = true;
    else if (a === '--json') args.json = true;
    else if (a === '--help' || a === '-h') args.help = true;
    else if (/^https:\/\/github\.com\/.+\/.+\/pull\/\d+/.test(a)) args.pr = a;
  }
  return args;
}

function printHelp() {
  console.log(`claude-review — Claude PR Reviewer ($150 Bounty #4)

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123 [options]

Options:
  --pr <url>        PR URL (required)
  --output <file>   Write Markdown to file (default: stdout)
  --comment         Post review as PR comment (requires GITHUB_TOKEN)
  --json            Also emit raw JSON alongside Markdown
  --help, -h        Show this help

Environment:
  ANTHROPIC_API_KEY  Anthropic API key (required for Claude review)
  GITHUB_TOKEN       GitHub token (optional, higher rate limit + commenting)

Model: ${MODEL}`);
}

function parsePrUrl(url) {
  const m = url.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!m) throw new Error(`Invalid PR URL: ${url}\nExpected https://github.com/owner/repo/pull/123`);
  return { owner: m[1], repo: m[2].replace(/\.git$/, ''), number: m[3] };
}

// ── GitHub API ─────────────────────────────────────────────────────────────
function ghHeaders(extra = {}) {
  const h = { 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'claude-pr-reviewer/1.0', ...extra };
  if (process.env.GITHUB_TOKEN) h['Authorization'] = `Bearer ${process.env.GITHUB_TOKEN}`;
  return h;
}

async function fetchJson(url, headers = ghHeaders()) {
  const res = await fetch(url, { headers });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`GitHub API ${res.status} for ${url}\n${body.slice(0, 500)}`);
  }
  return res.json();
}

async function fetchDiff(owner, repo, number) {
  const url = `https://api.github.com/repos/${owner}/${repo}/pulls/${number}`;
  const res = await fetch(url, { headers: ghHeaders({ 'Accept': 'application/vnd.github.v3.diff' }) });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`GitHub diff ${res.status} for ${url}\n${body.slice(0, 500)}`);
  }
  return res.text();
}

// ── Claude API ─────────────────────────────────────────────────────────────
function buildPrompt(pr, diff, files) {
  const filesSummary = files.map(f => `- ${f.filename} (${f.status} +${f.additions}/-${f.deletions})`).join('\n');
  const truncatedDiff = diff.length > MAX_DIFF_CHARS
    ? diff.slice(0, MAX_DIFF_CHARS) + `\n\n[... diff truncated: ${diff.length - MAX_DIFF_CHARS} chars omitted ...]`
    : diff;

  return `You are a senior code reviewer. Review this GitHub PR and return STRICT JSON only.

PR: #${pr.number} — ${pr.title}
Author: ${pr.user?.login}
Base: ${pr.base?.ref} <- Head: ${pr.head?.ref}
Description:
${(pr.body || '(no description)').slice(0, 2000)}

Changed files (${files.length}):
${filesSummary || '(none)'}

Diff:
\`\`\`diff
${truncatedDiff}
\`\`\`

Return a single JSON object with exactly these keys (no markdown wrapper):
{
  "summary": "2-3 sentences summarizing what changed and why",
  "risks": ["risk 1", "risk 2", ...],
  "suggestions": ["suggestion 1", "suggestion 2", ...],
  "confidence": "Low" | "Medium" | "High"
}

Rules:
- risks: concrete, specific to this diff (security, correctness, perf, breaking changes). 2-5 items. Empty array if none.
- suggestions: actionable improvements. 2-5 items.
- confidence: Low if diff is huge/ambiguous/binary, Medium if typical, High if small/reviewed thoroughly.
- Do not wrap in \`\`\`json fences. Raw JSON only.
- summary must be exactly 2-3 sentences.`;
}

async function callClaude(prompt) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) return null;
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': key,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 2048,
      messages: [{ role: 'user', content: prompt }],
    }),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`Anthropic API ${res.status}\n${body.slice(0, 1000)}`);
  }
  const data = await res.json();
  const text = data.content?.map(c => c.text || '').join('') || '';
  return text;
}

function parseClaudeJson(text) {
  // Strip optional fences
  let t = text.trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/i, '').trim();
  // Extract first {...} if extra prose slipped in
  const start = t.indexOf('{');
  const end = t.lastIndexOf('}');
  if (start !== -1 && end !== -1) t = t.slice(start, end + 1);
  return JSON.parse(t);
}

// ── Fallback heuristic review (no API key) ─────────────────────────────────
function fallbackReview(pr, diff, files) {
  const title = pr.title || '';
  const addCount = files.reduce((s, f) => s + f.additions, 0);
  const delCount = files.reduce((s, f) => s + f.deletions, 0);
  const binary = files.some(f => !f.patch && f.status === 'added');
  const large = diff.length > 50_000 || files.length > 15;

  return {
    summary: `PR #${pr.number} "${title}" modifies ${files.length} file(s) (+${addCount}/-${delCount}). `
      + (pr.body ? pr.body.slice(0, 180).replace(/\n/g, ' ') + '.' : 'No description provided.') + ' '
      + (large ? 'The change is large — review coverage may be partial.' : 'Change is focused and reviewable.'),
    risks: [
      ...(binary ? ['Binary or generated files included — verify they are intentional and not bloated.'] : []),
      ...(large ? ['Large diff increases risk of missed regressions — consider splitting.'] : []),
      'No automated test coverage visible in diff — confirm tests pass in CI.',
      'Review any credential or secret handling for accidental exposure.',
    ].slice(0, 4),
    suggestions: [
      'Add or update tests covering the changed paths.',
      'Ensure CI is green before merge (lint, test, build).',
      'Keep PR description and linked issue in sync for auditability.',
    ],
    confidence: large || binary ? 'Low' : 'Medium',
  };
}

// ── Markdown formatting ────────────────────────────────────────────────────
function toMarkdown(pr, review, opts = {}) {
  const prUrl = pr.html_url || `https://github.com/${opts.owner}/${opts.repo}/pull/${pr.number}`;
  const lines = [];
  lines.push(`## Claude Review — PR #${pr.number}`);
  lines.push('');
  lines.push(`> **${pr.title}** — [\`#${pr.number}\`](${prUrl}) by @${pr.user?.login || 'unknown'} | \`${pr.base?.ref || '?'} <- ${pr.head?.ref || '?'}\` | Model: \`${MODEL}\``);
  lines.push('');
  lines.push('### Summary');
  lines.push('');
  lines.push(review.summary?.trim() || '_No summary returned._');
  lines.push('');
  lines.push('### Risks');
  lines.push('');
  if (review.risks?.length) review.risks.forEach(r => lines.push(`- ${r}`));
  else lines.push('- No significant risks identified.');
  lines.push('');
  lines.push('### Suggestions');
  lines.push('');
  if (review.suggestions?.length) review.suggestions.forEach(s => lines.push(`- ${s}`));
  else lines.push('- No suggestions.');
  lines.push('');
  const conf = (review.confidence || 'Medium');
  const badge = conf === 'High' ? '🟢' : conf === 'Low' ? '🔴' : '🟡';
  lines.push(`### Confidence: ${badge} ${conf}`);
  lines.push('');
  if (opts.fallback) lines.push(`> _Heuristic fallback — set \`ANTHROPIC_API_KEY\` for a Claude-powered review._`);
  lines.push('');
  lines.push(`---`);
  lines.push(`<sub>Generated by <code>claude-review</code> · <code>${MODEL}</code> · ${new Date().toISOString()}</sub>`);
  return lines.join('\n');
}

// ── Post comment ───────────────────────────────────────────────────────────
async function postComment(owner, repo, number, body) {
  const url = `https://api.github.com/repos/${owner}/${repo}/issues/${number}/comments`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { ...ghHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ body }),
  });
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    throw new Error(`Post comment ${res.status}\n${t.slice(0, 800)}`);
  }
  return res.json();
}

// ── Main ───────────────────────────────────────────────────────────────────
async function main() {
  const args = parseArgs(process.argv);
  if (args.help || !args.pr) {
    printHelp();
    if (!args.pr && !args.help) process.exit(1);
    process.exit(0);
  }

  const { owner, repo, number } = parsePrUrl(args.pr);
  console.error(`→ Fetching PR #${number} from ${owner}/${repo} ...`);

  const pr = await fetchJson(`https://api.github.com/repos/${owner}/${repo}/pulls/${number}`);
  const [diff, files] = await Promise.all([
    fetchDiff(owner, repo, number),
    fetchJson(`https://api.github.com/repos/${owner}/${repo}/pulls/${number}/files?per_page=100`).catch(() => []),
  ]);

  // Truncate per-file patches to keep prompt bounded
  for (const f of files) {
    if (f.patch && f.patch.length > MAX_FILE_PATCH) {
      f.patch = f.patch.slice(0, MAX_FILE_PATCH) + '\n[... patch truncated ...]';
    }
  }

  console.error(`  PR: "${pr.title}" | ${files.length} files | diff ${diff.length} chars`);

  let review;
  let fallback = false;
  const prompt = buildPrompt(pr, diff, files);

  if (process.env.ANTHROPIC_API_KEY) {
    console.error(`→ Calling ${MODEL} ...`);
    const raw = await callClaude(prompt);
    try {
      review = parseClaudeJson(raw);
    } catch (e) {
      console.error(`  Claude returned non-JSON, wrapping as summary. Parse error: ${e.message}`);
      console.error(`  Raw (first 800 chars): ${String(raw).slice(0, 800)}`);
      review = { summary: String(raw).slice(0, 600), risks: ['Claude output was not structured JSON — review may be incomplete.'], suggestions: ['Re-run with a smaller diff or check ANTHROPIC_API_KEY.'], confidence: 'Low' };
    }
    // Validate shape
    if (!review.summary) review.summary = 'No summary returned.';
    if (!Array.isArray(review.risks)) review.risks = [];
    if (!Array.isArray(review.suggestions)) review.suggestions = [];
    if (!['Low', 'Medium', 'High'].includes(review.confidence)) review.confidence = 'Medium';
  } else {
    console.error('  No ANTHROPIC_API_KEY — using heuristic fallback.');
    review = fallbackReview(pr, diff, files);
    fallback = true;
  }

  const md = toMarkdown(pr, review, { owner, repo, fallback });

  if (args.output) {
    const { writeFileSync } = await import('fs');
    writeFileSync(args.output, md, 'utf8');
    console.error(`→ Wrote ${args.output} (${md.length} bytes)`);
  } else {
    process.stdout.write(md + '\n');
  }

  if (args.json) {
    const out = JSON.stringify({ pr: { number: pr.number, title: pr.title, url: pr.html_url }, review, model: MODEL }, null, 2);
    if (args.output) {
      const { writeFileSync } = await import('fs');
      const jpath = args.output.replace(/\.md$/, '.json');
      writeFileSync(jpath, out, 'utf8');
      console.error(`→ Wrote ${jpath}`);
    } else {
      console.error(out);
    }
  }

  if (args.comment) {
    if (!process.env.GITHUB_TOKEN) throw new Error('--comment requires GITHUB_TOKEN');
    console.error('→ Posting comment ...');
    const c = await postComment(owner, repo, number, md);
    console.error(`  Comment posted: ${c.html_url}`);
  }
}

main().catch(err => {
  console.error(`\n✖ ${err.message}`);
  if (process.env.DEBUG) console.error(err.stack);
  process.exit(1);
});
