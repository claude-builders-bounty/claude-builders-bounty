#!/usr/bin/env node
/**
 * claude-review — a Claude Code sub-agent runner that reviews a GitHub pull
 * request and emits (or posts) a structured Markdown review comment.
 *
 * Zero runtime dependencies. Requires Node 18+ (built-in fetch, AbortSignal).
 *
 * Pipeline
 *   1. Parse PR reference (URL or owner/repo + number)
 *   2. Fetch PR metadata + changed files via the GitHub REST API
 *   3. Build an analysis prompt (metadata + unified diff, size-truncated)
 *   4. Analyze:
 *        engine "claude"    -> run the `claude` CLI headless (Claude Code
 *                              sub-agent), prompt passed via stdin
 *        engine "heuristic" -> built-in deterministic diff analyzer (works
 *                              with no model and no network beyond the API)
 *        engine "auto"      -> claude if it is on PATH, else heuristic
 *   5. Print structured Markdown to stdout; with --comment, also post it as
 *      a comment on the PR (requires GITHUB_TOKEN with write access).
 *
 * Output contract (fixed sections, fixed order):
 *   ### Summary       2-3 sentences
 *   ### Risks         bullet list
 *   ### Suggestions   bullet list
 *   **Confidence:**   Low | Medium | High
 *
 * Exit codes: 0 ok, 1 usage, 2 GitHub API error, 3 engine error.
 */

import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { existsSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

/* ----------------------------- CLI configuration ------------------------ */

const DEFAULTS = {
  apiBase: (process.env.GITHUB_BASE_URL || 'https://api.github.com').replace(/\/$/, ''),
  engine: 'auto', // auto | claude | heuristic
  maxDiffChars: 60_000,
  maxFiles: 300,
  timeoutMs: 30_000,
  claudeTimeoutMs: 180_000,
};

function usage() {
  return `claude-review — review a GitHub PR with a Claude Code sub-agent and post a structured comment

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123 [options]
  claude-review --repo owner/repo --number 123 [options]
  claude-review --diff-file ./changes.diff            # offline mode, no API calls

Options:
  --pr <url>           GitHub pull request URL (https://github.com/o/r/pull/N)
  --repo <o/r>         Repository owner/name (alternative to --pr)
  --number <n>         PR number (used with --repo)
  --comment            Post the review as a comment on the PR (needs GITHUB_TOKEN)
  --engine <e>         claude | heuristic | auto (default: auto)
  --api-base <url>     GitHub API base (default: $GITHUB_BASE_URL or https://api.github.com)
  --diff-file <path>   Analyze a local diff file instead of fetching a PR (offline)
  --max-diff-chars <n> Truncate the diff sent to the model (default: 60000)
  --max-files <n>      Max changed files to fetch (default: 300)
  --timeout <ms>       GitHub API timeout (default: 30000)
  --claude-timeout <ms> Claude Code sub-agent timeout (default: 180000)
  -h, --help           Show this help

Environment:
  GITHUB_TOKEN         Personal access token / GitHub Actions token. Needed for
                       private repos and for --comment. Not needed for public reads.
  GITHUB_BASE_URL      GitHub Enterprise API base (e.g. https://ghe.corp.com/api/v3)
  ANTHROPIC_API_KEY    Required by the Claude Code CLI for the "claude" engine.

Output: structured Markdown on stdout (Summary / Risks / Suggestions / Confidence).
`;
}

function parseArgs(argv) {
  const cfg = { ...DEFAULTS, comment: false, help: false };
  const take = (i, name, value) => {
    if (value === undefined || value.startsWith('--')) {
      die(`Missing value for ${name}`, 1);
    }
    return value;
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case '--pr': cfg.pr = take(++i, a, argv[i]); break;
      case '--repo': cfg.repo = take(++i, a, argv[i]); break;
      case '--number': cfg.number = Number(take(++i, a, argv[i])); break;
      case '--comment': cfg.comment = true; break;
      case '--engine': {
        const v = take(++i, a, argv[i]);
        if (!['claude', 'heuristic', 'auto'].includes(v)) die(`Invalid --engine "${v}" (claude|heuristic|auto)`, 1);
        cfg.engine = v;
        break;
      }
      case '--api-base': cfg.apiBase = take(++i, a, argv[i]).replace(/\/$/, ''); break;
      case '--diff-file': cfg.diffFile = take(++i, a, argv[i]); break;
      case '--max-diff-chars': cfg.maxDiffChars = Number(take(++i, a, argv[i])); break;
      case '--max-files': cfg.maxFiles = Number(take(++i, a, argv[i])); break;
      case '--timeout': cfg.timeoutMs = Number(take(++i, a, argv[i])); break;
      case '--claude-timeout': cfg.claudeTimeoutMs = Number(take(++i, a, argv[i])); break;
      case '-h': case '--help': cfg.help = true; break;
      default: die(`Unknown option: ${a}\n\n${usage()}`, 1);
    }
  }
  for (const k of ['maxDiffChars', 'maxFiles', 'timeoutMs', 'claudeTimeoutMs']) {
    if (!Number.isFinite(cfg[k]) || cfg[k] <= 0) die(`Invalid numeric value for --${k.replace(/Ms$/, 'ms').replace(/(chars|files)/, '$1')}`, 1);
  }
  return cfg;
}

function die(message, code) {
  process.stderr.write(`claude-review: ${message}\n`);
  process.exit(code);
}

/* ------------------------------ GitHub client --------------------------- */

function authHeaders(cfg) {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
  return {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': 'claude-review/1.0',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function apiRequest(cfg, method, urlPath, body) {
  const url = `${cfg.apiBase}${urlPath}`;
  let res;
  try {
    res = await fetch(url, {
      method,
      headers: { ...authHeaders(cfg), ...(body ? { 'Content-Type': 'application/json' } : {}) },
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(cfg.timeoutMs),
    });
  } catch (err) {
    throw Object.assign(new Error(`GitHub API request failed for ${url}: ${err.message}`), { code: 2, url });
  }

  if (res.status === 403 || res.status === 429) {
    const remaining = res.headers.get('x-ratelimit-remaining');
    const reset = res.headers.get('x-ratelimit-reset');
    const when = reset ? new Date(Number(reset) * 1000).toISOString() : 'soon';
    throw Object.assign(
      new Error(
        remaining === '0'
          ? `GitHub API rate limit exhausted (resets ${when}). Retry later, or set GITHUB_TOKEN for a higher limit.`
          : `GitHub API returned ${res.status} for ${url} (check token permissions).`,
      ),
      { code: 2, url },
    );
  }
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw Object.assign(new Error(`GitHub API ${res.status} for ${url}: ${text.slice(0, 300)}`), { code: 2, url });
  }
  return res;
}

export function parsePrUrl(raw) {
  const m = String(raw).match(/github\.com\/([\w.-]+)\/([\w.-]+)\/pull\/(\d+)/i);
  if (!m) return null;
  return { owner: m[1], repo: m[2], number: Number(m[3]) };
}

async function fetchPr(cfg, ref) {
  const { owner, repo, number } = ref;
  const metaRes = await apiRequest(cfg, 'GET', `/repos/${owner}/${repo}/pulls/${number}`);
  const pr = await metaRes.json();

  const files = [];
  let page = 1;
  let next = `/repos/${owner}/${repo}/pulls/${number}/files?per_page=100&page=1`;
  while (next && files.length < cfg.maxFiles) {
    const res = await apiRequest(cfg, 'GET', next);
    const batch = await res.json();
    files.push(...batch);
    const link = res.headers.get('link') || '';
    const m = link.match(/<([^>]+)>;\s*rel="next"/);
    next = m ? m[1].replace(/^https?:\/\/[^/]+/, '') : null;
    if (files.length >= cfg.maxFiles) {
      cfg.truncatedFiles = true;
      break;
    }
    page += 1;
  }

  const additions = pr.additions || files.reduce((s, f) => s + (f.additions || 0), 0);
  const deletions = pr.deletions || files.reduce((s, f) => s + (f.deletions || 0), 0);

  return {
    owner,
    repo,
    number,
    title: pr.title || '(untitled)',
    author: (pr.user && pr.user.login) || 'unknown',
    body: (pr.body || '').slice(0, 2000),
    url: pr.html_url || `https://github.com/${owner}/${repo}/pull/${number}`,
    state: pr.state || 'unknown',
    merged: Boolean(pr.merged_at),
    baseSha: (pr.base && pr.base.sha || '').slice(0, 12),
    headSha: (pr.head && pr.head.sha || '').slice(0, 12),
    files: files.map((f) => ({
      filename: f.filename,
      status: f.status, // added | modified | removed | renamed
      additions: f.additions || 0,
      deletions: f.deletions || 0,
      patch: typeof f.patch === 'string' ? f.patch : null,
      binary: !f.patch && f.additions + f.deletions === 0,
    })),
    additions,
    deletions,
  };
}

/* ------------------------- Offline diff (fixture) mode ------------------- */

/**
 * Parse a unified diff file into the same `files` shape used by fetchPr().
 * Good enough for offline tests and local use.
 */
export function parseDiffFile(text) {
  const files = [];
  let cur = null;
  for (const line of text.split(/\r?\n/)) {
    const git = line.match(/^diff --git a\/(.+) b\/(.+)$/);
    const plus = line.match(/^\+\+\+ b\/(.+)$/);
    const minus = line.match(/^--- a\/(.+)$/);
    if (git) {
      cur = { filename: git[2], status: 'modified', additions: 0, deletions: 0, patch: [] };
      files.push(cur);
      continue;
    }
    if (!cur) continue;
    if (plus) cur.filename = plus[1];
    if (line.startsWith('---') || line.startsWith('+++') || line.startsWith('diff ')) continue;
    if (line.startsWith('+') && !line.startsWith('+++')) {
      cur.additions += 1;
      cur.patch.push(line);
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      cur.deletions += 1;
      cur.patch.push(line);
    } else if (line.startsWith(' ')) {
      cur.patch.push(line);
    } else if (line.startsWith('@@') || line.startsWith('index ')) {
      cur.patch.push(line);
    }
  }
  for (const f of files) {
    const added = f.patch.filter((l) => l.startsWith('+') && !l.startsWith('+++')).length > 0;
    const removed = f.patch.filter((l) => l.startsWith('-') && !l.startsWith('---')).length > 0;
    f.status = added && removed ? 'modified' : added ? 'added' : removed ? 'removed' : 'modified';
    f.patch = f.patch.join('\n') || null;
    f.binary = false;
  }
  return files;
}

/* ------------------------------ Prompt building -------------------------- */

function buildDiffText(ctx) {
  let text = '';
  for (const f of ctx.files) {
    const status = f.status ? ` [${f.status}]` : '';
    text += `### ${f.filename}${status} (+${f.additions}/-${f.deletions})\n`;
    text += f.patch ? `${f.patch}\n` : '[no patch available (binary or unchanged)]\n';
    text += '\n';
  }
  return text;
}

export function buildPrompt(ctx, cfg) {
  const diff = buildDiffText(ctx);
  const truncated = diff.length > cfg.maxDiffChars;
  const diffPart = truncated ? diff.slice(0, cfg.maxDiffChars) + '\n[... diff truncated ...]' : diff;
  const meta = [
    `title: ${ctx.title}`,
    `author: ${ctx.author}`,
    `repository: ${ctx.owner}/${ctx.repo}`,
    `number: ${ctx.number}`,
    `files changed: ${ctx.files.length}`,
    `additions: ${ctx.additions}, deletions: ${ctx.deletions}`,
    `base: ${ctx.baseSha || 'n/a'}, head: ${ctx.headSha || 'n/a'}`,
    `description: ${(ctx.body || '(none)').slice(0, 1500) || '(none)'}`,
  ].join('\n');

  return `You are a precise senior software reviewer running as a headless Claude Code sub-agent.
Analyze the pull request below and output ONLY a Markdown review comment — no preamble, no trailing commentary, no outer code fences — with exactly these sections in this order:

## 🤖 PR Review — ${ctx.owner}/${ctx.repo}#${ctx.number}

### Summary
Two to three sentences describing what this PR changes and why it likely exists.

### Risks
- One bullet per identified risk, specific to file paths or code shown. If none, write "- None identified."

### Suggestions
- One bullet per concrete improvement. If none, write "- None."

**Confidence:** Low
(Use exactly one of: Low, Medium, High. High only if the diff fully covers the change and you have no material doubts.)

Rules:
- Base every claim on the diff and metadata shown. Do not invent behavior.
- Do not use any tools; answer directly.
- Keep the whole comment under ~500 words.

=== METADATA ===
${meta}

=== DIFF ===
${diffPart}
`;
}

export function validateReview(text) {
  return (
    /###\s+Summary/i.test(text) &&
    /###\s+Risks/i.test(text) &&
    /###\s+Suggestions/i.test(text) &&
    /\*\*Confidence:\*\*\s*(Low|Medium|High)\b/i.test(text)
  );
}

function renderReview({ ctx, summary, risks, suggestions, confidence, engine, note }) {
  const lines = [
    `## 🤖 PR Review — ${ctx.owner}/${ctx.repo}#${ctx.number}`,
    '',
    `> Generated by claude-review · engine: ${engine} · ${new Date().toISOString()}`,
    '',
    '### Summary',
    summary,
    '',
    '### Risks',
    ...risks.map((r) => `- ${r}`),
    '',
    '### Suggestions',
    ...suggestions.map((s) => `- ${s}`),
    '',
    `**Confidence:** ${confidence}`,
  ];
  if (note) lines.push('', `> ${note}`);
  return lines.join('\n');
}

/* --------------------------- Heuristic analyzer -------------------------- */

const RISK_PATTERNS = [
  { risk: 'Possible hardcoded credential or secret in code', sug: 'Move secrets to environment variables or a secret manager; rotate anything already committed.', re: /(api[_-]?key|apikey|secret|passwd|password|access[_-]?token|auth[_-]?token)\s*[:=]\s*['"][^'"\s]{6,}/i },
  { risk: 'Dynamic code execution (eval / new Function)', sug: 'Avoid eval; use a safe expression parser or explicit handlers.', re: /\b(eval|new\s+Function)\s*\(/ },
  { risk: 'Non-TLS (http://) endpoint referenced', sug: 'Prefer HTTPS endpoints to avoid unencrypted transport.', re: /http:\/\/(?!localhost|127\.0\.0\.1|0\.0\.0\.0)/ },
  { risk: 'Shell pipeline installing from remote (curl | sh)', sug: 'Pin and verify the artifact being installed instead of piping remote scripts to a shell.', re: /curl[^\n|]*\|\s*(ba|z)?sh/ },
  { risk: 'TODO/FIXME markers left in code', sug: 'File issues for the TODO/FIXME markers or resolve them in this PR.', re: /\b(TODO|FIXME|HACK|XXX)\b/ },
];

const TEST_PATH_RE = /(^|\/)(tests?|__tests__|spec|specs|cypress|playwright)\b|\.test\.[cm]?[jt]sx?$|\.spec\.[cm]?[jt]sx?$|conftest\.py$/;
const LOCKFILE_RE = /(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|bun\.lockb|Cargo\.lock|go\.sum|Gemfile\.lock|poetry\.lock|uv\.lock|composer\.lock)$/;
const CI_PATH_RE = /(^|\/)\.github\/workflows\/|^\.github\/workflows\/|^Jenkinsfile$|^\.gitlab-ci\.yml$|^\.circleci/;
const SECURITY_PATH_RE = /(auth|authenticat|authoriz|security|crypto|password|credential|secret|permission)/i;
const DOC_PATH_RE = /\.(md|rst|txt|adoc|tex)$/i;

function isDocFile(f) {
  return DOC_PATH_RE.test(f.filename) || /(^|\/)docs?\b/i.test(f.filename);
}

function countPatchLines(patch) {
  let add = 0;
  let del = 0;
  if (!patch) return { add, del };
  for (const line of patch.split(/\r?\n/)) {
    if (line.startsWith('+') && !line.startsWith('+++')) add += 1;
    else if (line.startsWith('-') && !line.startsWith('---')) del += 1;
  }
  return { add, del };
}

export function heuristicReview(ctx, cfg) {
  const files = ctx.files;
  const risks = [];
  const suggestions = [];
  const pushRisk = (r, s) => {
    if (!risks.includes(r)) risks.push(r);
    if (s && !suggestions.includes(s)) suggestions.push(s);
  };

  const newCount = files.filter((f) => f.status === 'added').length;
  const modCount = files.filter((f) => f.status === 'modified').length;
  const remCount = files.filter((f) => f.status === 'removed').length;
  const totalLines = files.reduce((s, f) => s + f.additions + f.deletions, 0);

  // Scan added lines for risky patterns.
  for (const f of files) {
    if (!f.patch) continue;
    for (const line of f.patch.split(/\r?\n/)) {
      if (!line.startsWith('+') || line.startsWith('+++')) continue;
      for (const p of RISK_PATTERNS) {
        if (p.re.test(line)) pushRisk(`${p.risk} (${f.filename})`, p.sug);
      }
    }
  }

  // File-level checks.
  for (const f of files) {
    const base = path.posix.basename(f.filename);
    if (/^\.env(\..+)?$/.test(base) && (f.status === 'added' || f.status === 'modified')) {
      pushRisk(`Committed \`.env\` file may contain real credentials (${f.filename})`, 'Stop committing .env files; use .env.example with placeholders and rotate exposed values.');
    }
    if (LOCKFILE_RE.test(base)) {
      pushRisk(`Dependency lockfile changed (${f.filename})`, 'Review which dependency versions changed and run the full test suite against the new resolution.');
    }
    if (CI_PATH_RE.test(f.filename)) {
      pushRisk('CI/CD pipeline configuration changed', 'Verify workflow triggers, permissions, and that required checks still run on forks as intended.');
    }
    if (f.status === 'removed' && TEST_PATH_RE.test(f.filename)) {
      pushRisk(`Test file removed (${f.filename})`, 'Confirm coverage for the removed tests is preserved elsewhere.');
    }
    if (f.additions + f.deletions > 500) {
      pushRisk(`Large single-file change (${f.filename}, ${f.additions + f.deletions} lines)`, 'Break the change into focused commits or split the PR to make review safer.');
    }
    if (SECURITY_PATH_RE.test(f.filename)) {
      pushRisk(`Change touches auth/security-sensitive code (${f.filename})`, 'Give the security-relevant hunks extra review attention and add regression tests.');
    }
  }

  const isNonDocSource = (f) =>
    !f.binary && !TEST_PATH_RE.test(f.filename) && !isDocFile(f) && !path.posix.basename(f.filename).startsWith('.');
  const sourceChanged = files.some(isNonDocSource);
  const testsChanged = files.some((f) => TEST_PATH_RE.test(f.filename));
  if (sourceChanged && !testsChanged) {
    pushRisk('No test files changed although source code changed', 'Add or update automated tests covering the changed behavior before merging.');
  }
  const docsOnly = files.length > 0 && files.every((f) => isDocFile(f) || path.posix.basename(f.filename).startsWith('.'));
  if (docsOnly) {
    suggestions.push('This looks like a documentation-only PR; verify the updated content matches current behavior and examples.');
  }

  const truncated = Boolean(cfg.diffTruncated) || Boolean(cfg.truncatedFiles);
  const binaryOnly = files.length > 0 && files.every((f) => f.binary || !f.patch);
  if (binaryOnly) risks.push('Diff contains only binary or unparsed files; content could not be inspected');

  if (risks.length === 0) risks.push('None identified.');

  // Suggestions not tied to a specific risk.
  if (!ctx.body) suggestions.push('The PR has no description; add what/why/how-tested to make review and release notes easier.');
  if (files.length > 15) suggestions.push(`The PR touches ${files.length} files; consider splitting it into smaller, focused PRs.`);
  if (risks.length === 0 && suggestions.length === 0) suggestions.push('Re-run the full test suite on the merge commit before release.');
  if (!suggestions.some((s) => /test/i.test(s))) suggestions.push('Re-run the full test suite locally on the merge commit before release.');

  // Summary: exactly three sentences.
  const topDirs = [...new Set(files.map((f) => {
    const d = path.posix.dirname(f.filename);
    return d === '' || d === '.' || d === '/' ? '(root)' : d;
  }))].slice(0, 3).join(', ');
  const intent = titleIntent(ctx.title);
  const s1 = `This PR (“${ctx.title}”, by ${ctx.author}) changes ${files.length} file${files.length === 1 ? '' : 's'} in ${ctx.owner}/${ctx.repo}, adding ${ctx.additions} line${ctx.additions === 1 ? '' : 's'} and removing ${ctx.deletions} line${ctx.deletions === 1 ? '' : 's'}.`;
  const s2 = `The changes touch ${topDirs} and consist of ${newCount} added, ${modCount} modified, and ${remCount} removed file${files.length === 1 ? '' : 's'}.`;
  const s3 = intent;
  const summary = `${s1} ${s2} ${s3}`;

  // Confidence.
  let score = 3; // High
  if (truncated) score -= 1;
  if (totalLines < 10) score -= 1;
  if (binaryOnly) score -= 1;
  score = Math.min(score, 2); // heuristic engine caps at Medium
  const confidence = ['Low', 'Medium', 'High'][score - 1];

  return renderReview({ ctx, summary, risks, suggestions, confidence, engine: 'heuristic-fallback' });
}

function titleIntent(title) {
  const t = title.toLowerCase();
  if (/^\[(?:(?:feat|feature|fix|bug|docs?|chore|refactor|test|perf|ci|build)\b.*)*]?\s*|^(feat|fix|docs|chore|refactor|test|perf|ci|build)(\(|:)/.test(t)) {
    if (t.startsWith('feat')) return 'The title prefix suggests it introduces new functionality.';
    if (t.startsWith('fix')) return 'The title prefix suggests it fixes a bug.';
    if (t.startsWith('docs')) return 'The title prefix suggests a documentation update.';
    if (t.startsWith('refactor')) return 'The title prefix suggests a refactor with no intended behavior change.';
    if (t.startsWith('chore')) return 'The title prefix suggests routine maintenance.';
  }
  return 'Based on the diff, it appears to be a maintenance-style update to the codebase.';
}

/* ------------------------------ Claude engine ---------------------------- */

function claudeOnPath() {
  const where = process.platform === 'win32' ? 'where' : 'which';
  try {
    const { execSync } = require('node:child_process');
    return execSync(`${where} claude`, { stdio: ['ignore', 'ignore', 'ignore'] }).length > 0;
  } catch {
    return false;
  }
}

function runClaudeHeadless(prompt, cfg) {
  return new Promise((resolve, reject) => {
    let stdout = '';
    let stderr = '';
    const args = ['-p', '--output-format', 'text'];
    const proc = spawn('claude', args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: process.platform === 'win32',
    });
    const timer = setTimeout(() => {
      proc.kill('SIGTERM');
      reject(new Error(`Claude Code sub-agent timed out after ${cfg.claudeTimeoutMs} ms`));
    }, cfg.claudeTimeoutMs);
    proc.stdout.on('data', (d) => { stdout += d; });
    proc.stderr.on('data', (d) => { stderr += d; });
    proc.on('error', (err) => {
      clearTimeout(timer);
      reject(new Error(`Failed to start claude: ${err.message}`));
    });
    proc.on('close', (code) => {
      clearTimeout(timer);
      if (code !== 0) reject(new Error(`claude exited with code ${code}: ${stderr.trim().slice(0, 400)}`));
      else resolve(stdout);
    });
    proc.stdin.on('error', () => { /* EPIPE when the child exits early */ });
    proc.stdin.write(prompt);
    proc.stdin.end();
  });
}

async function analyze(ctx, cfg) {
  const engine = cfg.engine === 'auto' ? (claudeOnPath() ? 'claude' : 'heuristic') : cfg.engine;
  cfg.chosenEngine = engine;

  if (engine === 'claude') {
    const prompt = buildPrompt(ctx, { ...cfg, diffTruncated: ctx.diffTruncated });
    let text;
    try {
      text = await runClaudeHeadless(prompt, cfg);
    } catch (err) {
      if (cfg.engine === 'claude') die(`Claude engine failed: ${err.message}`, 3);
      process.stderr.write(`claude-review: Claude engine unavailable (${err.message}); falling back to heuristic analyzer.\n`);
      cfg.chosenEngine = 'heuristic';
      return heuristicReview(ctx, cfg);
    }
    text = text.trim();
    if (!validateReview(text)) {
      if (cfg.engine === 'claude') die('Claude output did not match the required review structure.', 3);
      process.stderr.write('claude-review: Claude output failed validation; falling back to heuristic analyzer.\n');
      cfg.chosenEngine = 'heuristic';
      return heuristicReview(ctx, cfg);
    }
    return text;
  }

  return heuristicReview(ctx, cfg);
}

/* ------------------------------ Comment posting -------------------------- */

async function postComment(cfg, ctx, body) {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
  if (!token) {
    die('--comment requires GITHUB_TOKEN (or GH_TOKEN) with write access to the target repo.', 2);
  }
  const url = `${cfg.apiBase}/repos/${ctx.owner}/${ctx.repo}/issues/${ctx.number}/comments`;
  const res = await apiRequest(cfg, 'POST', `/repos/${ctx.owner}/${ctx.repo}/issues/${ctx.number}/comments`, { body });
  const json = await res.json().catch(() => ({}));
  return json.html_url || url;
}

/* ---------------------------------- Main ----------------------------------- */

async function main() {
  const cfg = parseArgs(process.argv.slice(2));
  if (cfg.help) {
    process.stdout.write(usage());
    return 0;
  }

  // Fail fast on impossible/forbidden combinations before any network access.
  if (cfg.comment && cfg.diffFile) {
    die('--comment requires a target PR; it is not available in --diff-file mode. Use --pr instead.', 1);
  }
  if (cfg.comment && !(process.env.GITHUB_TOKEN || process.env.GH_TOKEN)) {
    die('--comment requires GITHUB_TOKEN (or GH_TOKEN) with write access to the target repo.', 2);
  }

  let ctx;
  if (cfg.diffFile) {
    let text;
    try {
      text = readFileSync(cfg.diffFile, 'utf8');
    } catch (err) {
      die(`Cannot read --diff-file: ${err.message}`, 1);
    }
    const files = parseDiffFile(text);
    ctx = {
      owner: 'local',
      repo: 'diff',
      number: 0,
      title: path.basename(cfg.diffFile),
      author: 'offline',
      body: '',
      url: 'offline',
      state: 'offline',
      merged: false,
      baseSha: '',
      headSha: '',
      files,
      additions: files.reduce((s, f) => s + f.additions, 0),
      deletions: files.reduce((s, f) => s + f.deletions, 0),
    };
  } else {
    const ref = cfg.pr ? parsePrUrl(cfg.pr) : cfg.repo && cfg.number ? { owner: cfg.repo.split('/')[0], repo: cfg.repo.split('/')[1], number: cfg.number } : null;
    if (!ref) die('Provide --pr <github pull request URL> or --repo <owner/repo> --number <n>.\n\n' + usage(), 1);
    if (!Number.isInteger(ref.number) || ref.number <= 0) die(`Invalid PR number: ${ref.number}`, 1);
    try {
      ctx = await fetchPr(cfg, ref);
    } catch (err) {
      die(err.message, err.code || 2);
    }
  }

  ctx.diffTruncated = buildDiffText(ctx).length > cfg.maxDiffChars;

  const review = await analyze(ctx, cfg);

  if (cfg.comment) {
    const url = await postComment(cfg, ctx, review);
    process.stderr.write(`claude-review: comment posted: ${url}\n`);
  }

  process.stdout.write(review + '\n');
  process.stderr.write(`claude-review: engine used: ${cfg.chosenEngine}\n`);
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().then(
    (code) => process.exit(code),
    (err) => {
      process.stderr.write(`claude-review: ${err.message}\n`);
      process.exit(err.code || 2);
    },
  );
}

// Functions needed by the test suite are exported at their declaration sites
// (parsePrUrl, buildPrompt, validateReview, parseDiffFile, heuristicReview).
