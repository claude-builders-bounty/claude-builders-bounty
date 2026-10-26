#!/usr/bin/env node
/**
 * Offline test suite for claude-review (zero dependencies).
 * Runs: node test/run-tests.mjs
 *
 * Covers: URL parsing, offline diff analysis, required output sections,
 * confidence values, error handling (bad URL, --comment without token).
 * No network access is required.
 */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

import { parsePrUrl, validateReview, parseDiffFile, heuristicReview, buildPrompt } from '../bin/claude-review.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const CLI = path.join(here, '..', 'bin', 'claude-review.mjs');
const FIXTURE = path.join(here, 'fixtures', 'sample.diff');

let passed = 0;
let failed = 0;
const failures = [];

function test(name, fn) {
  try {
    fn();
    passed += 1;
    console.log(`  ok    ${name}`);
  } catch (err) {
    failed += 1;
    failures.push({ name, err });
    console.log(`  FAIL  ${name}\n        ${err.message}`);
  }
}

function runCli(args, env) {
  const res = spawnSync(process.execPath, [CLI, ...args], {
    encoding: 'utf8',
    env: { ...process.env, ...(env || {}) },
    timeout: 30_000,
  });
  return res;
}

const REQUIRED_SECTIONS = [/###\s+Summary/i, /###\s+Risks/i, /###\s+Suggestions/i, /\*\*Confidence:\*\*\s*(Low|Medium|High)\b/i];

console.log('parsePrUrl');
test('parses a standard PR URL', () => {
  const r = parsePrUrl('https://github.com/owner/repo/pull/123');
  assert.deepEqual(r, { owner: 'owner', repo: 'repo', number: 123 });
});
test('parses URL with case/whitespace', () => {
  const r = parsePrUrl('  https://GitHub.com/Some-Org/my.repo/pull/9999  ');
  assert.deepEqual(r, { owner: 'Some-Org', repo: 'my.repo', number: 9999 });
});
test('rejects non-PR URLs and junk', () => {
  assert.equal(parsePrUrl('not a url'), null);
  assert.equal(parsePrUrl('https://github.com/owner/repo/issues/123'), null);
  assert.equal(parsePrUrl('https://github.com/owner/repo/pull/'), null);
});

console.log('offline diff analysis (--diff-file)');
test('fixture diff parses into 5 files', () => {
  const files = parseDiffFile(readFileSync(FIXTURE, 'utf8'));
  assert.equal(files.length, 5);
  assert.equal(files.find((f) => f.filename === '.env').status, 'added');
  assert.equal(files.find((f) => f.filename === 'test/auth.test.js').status, 'removed');
});
test('heuristic review has all required sections and valid confidence', () => {
  const files = parseDiffFile(readFileSync(FIXTURE, 'utf8'));
  const ctx = {
    owner: 'local', repo: 'diff', number: 0, title: 'sample.diff', author: 'offline',
    body: '', url: 'offline', state: 'offline', merged: false, baseSha: '', headSha: '',
    files,
    additions: files.reduce((s, f) => s + f.additions, 0),
    deletions: files.reduce((s, f) => s + f.deletions, 0),
  };
  const out = heuristicReview(ctx, { diffTruncated: false, truncatedFiles: false });
  for (const re of REQUIRED_SECTIONS) assert.ok(re.test(out), `missing section ${re}`);
  assert.ok(['Low', 'Medium', 'High'].includes(/Confidence:\*\*\s*(\w+)/.exec(out)[1]));
});
test('heuristic review flags the seeded risks', () => {
  const files = parseDiffFile(readFileSync(FIXTURE, 'utf8'));
  const ctx = {
    owner: 'local', repo: 'diff', number: 0, title: 'sample.diff', author: 'offline',
    body: '', url: 'offline', state: 'offline', merged: false, baseSha: '', headSha: '',
    files,
    additions: files.reduce((s, f) => s + f.additions, 0),
    deletions: files.reduce((s, f) => s + f.deletions, 0),
  };
  const out = heuristicReview(ctx, { diffTruncated: false, truncatedFiles: false });
  assert.ok(/credential|secret/i.test(out), 'expected a secret/credential risk');
  assert.ok(/eval/i.test(out), 'expected an eval risk');
  assert.ok(/\.env/i.test(out), 'expected a .env risk');
  assert.ok(/Test file removed/i.test(out), 'expected a removed-test risk');
  assert.ok(/lockfile/i.test(out), 'expected a lockfile risk');
  // A test file WAS changed (removed), so the missing-tests risk must be suppressed.
  assert.ok(!/No test files changed/i.test(out), 'missing-tests risk should be suppressed when a test file changed');
});
test('prompt contains diff, metadata, and output contract', () => {
  const files = parseDiffFile(readFileSync(FIXTURE, 'utf8'));
  const ctx = {
    owner: 'owner', repo: 'repo', number: 42, title: 'Add feature', author: 'dev',
    body: 'Why: demo', url: 'u', state: 'open', merged: false, baseSha: 'b', headSha: 'h',
    files,
    additions: files.reduce((s, f) => s + f.additions, 0),
    deletions: files.reduce((s, f) => s + f.deletions, 0),
  };
  const prompt = buildPrompt(ctx, { maxDiffChars: 100_000 });
  assert.ok(prompt.includes('### Summary') && prompt.includes('### Risks') && prompt.includes('### Suggestions'));
  assert.ok(prompt.includes('src/auth.js'));
  assert.ok(prompt.includes('title: Add feature'));
  assert.ok(prompt.includes('owner/repo#42'));
});

console.log('CLI end-to-end (offline)');
test('--diff-file run prints a complete structured review (exit 0)', () => {
  const res = runCli(['--diff-file', FIXTURE, '--engine', 'heuristic']);
  assert.equal(res.status, 0, `stderr: ${res.stderr}`);
  for (const re of REQUIRED_SECTIONS) assert.ok(re.test(res.stdout), `missing ${re}`);
  assert.ok(/engine used: heuristic/.test(res.stderr));
});
test('summary is 2-3 sentences in heuristic mode', () => {
  const res = runCli(['--diff-file', FIXTURE, '--engine', 'heuristic']);
  const m = res.stdout.match(/### Summary\n([\s\S]*?)\n\n/);
  assert.ok(m, 'summary section found');
  const sentences = m[1].trim().split(/\. (?=[A-Z])/).length;
  assert.ok(sentences >= 2 && sentences <= 3, `expected 2-3 sentences, got ${sentences}`);
});
test('--pr with invalid URL exits 1 with usage hint', () => {
  const res = runCli(['--pr', 'https://example.com/nope']);
  assert.equal(res.status, 1);
  assert.ok(/github\.com|Provide --pr/i.test(res.stderr));
});
test('no arguments exits 1 with usage', () => {
  const res = runCli([]);
  assert.equal(res.status, 1);
  assert.ok(/claude-review/i.test(res.stderr + res.stdout));
});
test('--comment in --diff-file mode exits 1 (no target PR, no network)', () => {
  const res = runCli(['--diff-file', FIXTURE, '--comment'], { GITHUB_TOKEN: '', GH_TOKEN: '' });
  assert.equal(res.status, 1, `stderr: ${res.stderr}`);
  assert.ok(/target PR/i.test(res.stderr));
});
test('--comment without GITHUB_TOKEN fails fast with exit 2 (no network)', () => {
  const res = runCli(['--pr', 'https://github.com/example/owner/pull/5', '--comment'], { GITHUB_TOKEN: '', GH_TOKEN: '' });
  assert.equal(res.status, 2, `stderr: ${res.stderr}`);
  assert.ok(/GITHUB_TOKEN/i.test(res.stderr));
});
test('--help prints usage and exits 0', () => {
  const res = runCli(['--help']);
  assert.equal(res.status, 0);
  assert.ok(res.stdout.includes('Usage:'));
});

console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) {
  for (const f of failures) console.error(`- ${f.name}: ${f.err.message}`);
  process.exit(1);
}
process.exit(0);
