import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { assess, prompt, runSmoke } from './context-smoke.mjs';

const response = { type: 'result', subtype: 'success', is_error: false,
  usage: { output_tokens: 10 }, result: 'A plan requiring human review.' };
const ok = () => ({ status: 0, stdout: JSON.stringify(response) });

test('nonzero status, timeout and signal fail closed without exposing raw output', () => {
  for (const result of [{ status: 1, stderr: 'private token' },
    { status: 0, error: new Error('private path') }, { status: null, signal: 'SIGTERM' }]) {
    const report = assess(result);
    assert.equal(report.status, 'blocked');
    assert.equal(report.acceptance_passed, false);
    assert(!JSON.stringify(report).includes('private'));
  }
});

test('success subtype with is_error true is not success', () => {
  assert.equal(assess({ status: 0, stdout: JSON.stringify({ ...response, is_error: true, api_error_status: 401 }) }).status, 'blocked');
});

test('invalid JSON, missing flags and zero-token or empty responses fail closed', () => {
  for (const data of ['not JSON', 'null', '{}', JSON.stringify({ ...response, usage: { output_tokens: 0 } }),
    JSON.stringify({ ...response, result: ' ' })]) {
    assert.equal(assess({ status: 0, stdout: data }).status, 'blocked');
  }
});

test('even a successful response requires manual semantic review', () => {
  assert.deepEqual(assess(ok()), { status: 'review_required', acceptance_passed: false });
});

test('fresh project copies exact guidance, disables tools/MCP, and is cleaned', () => {
  let cwd;
  const report = runSmoke({ execute(binary, args, options) {
    cwd = options.cwd;
    assert.equal(binary, 'claude');
    assert.equal(readFileSync(join(cwd, 'CLAUDE.md'), 'utf8'), readFileSync(new URL('../CLAUDE.md', import.meta.url), 'utf8'));
    assert(existsSync(join(cwd, 'src/app/page.tsx')));
    assert.equal(args[args.indexOf('--tools') + 1], '');
    assert(args.includes('--strict-mcp-config'));
    assert.equal(args[args.indexOf('--mcp-config') + 1], '{"mcpServers":{}}');
    assert.equal(options.timeout, 90000);
    assert(!args.includes('--dangerously-skip-permissions'));
    assert(!prompt.includes('Do not ask'));
    return ok();
  } });
  assert.equal(report.status, 'review_required');
  assert(!existsSync(cwd));
});

test('cleanup also runs when process invocation throws', () => {
  let cwd;
  assert.throws(() => runSmoke({ execute(_binary, _args, options) { cwd = options.cwd; throw Error('failed'); } }));
  assert(!existsSync(cwd));
});

test('response output is opt-in, private and never overwrites an existing file', () => {
  const dir = mkdtempSync(join(tmpdir(), 'context-report-test-'));
  const target = join(dir, 'response.txt');
  try {
    assert.equal(runSmoke({ execute: ok, responseFile: target }).response_saved, true);
    assert.equal(readFileSync(target, 'utf8'), response.result + '\n');
    if (process.platform !== 'win32') assert.equal(statSync(target).mode & 0o777, 0o600);
    writeFileSync(target, 'keep');
    assert.throws(() => runSmoke({ execute: ok, responseFile: target }), { code: 'EEXIST' });
    assert.equal(readFileSync(target, 'utf8'), 'keep');
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
