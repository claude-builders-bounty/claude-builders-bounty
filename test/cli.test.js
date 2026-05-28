import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import { resolve } from 'path';

const CLI = resolve(import.meta.dirname, '..', 'bin', 'claude-review.js');
const PKG = JSON.parse(readFileSync(resolve(import.meta.dirname, '..', 'package.json'), 'utf-8'));

describe('claude-review CLI', () => {

  it('--version prints correct version', () => {
    const out = execSync('node ' + CLI + ' --version', { encoding: 'utf-8' }).trim();
    assert.equal(out, PKG.version);
  });

  it('--help prints usage', () => {
    const out = execSync('node ' + CLI + ' --help', { encoding: 'utf-8' }).trim();
    assert.ok(out.includes('claude-review'));
    assert.ok(out.includes('--pr'));
  });

  it('fails without --pr flag', () => {
    try {
      execSync('node ' + CLI, { encoding: 'utf-8' });
      assert.fail('Should have thrown');
    } catch (e) {
      assert.ok(true);
    }
  });

  it('fails with invalid PR URL', () => {
    try {
      execSync('node ' + CLI + ' --pr https://example.com', { encoding: 'utf-8' });
      assert.fail('Should have thrown');
    } catch (e) {
      assert.ok(e.stderr.includes('Error'));
    }
  });

  it('reviews a real PR and outputs structured Markdown (Test PR 1)', () => {
    const out = execSync(
      'node ' + CLI + ' --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2234',
      { encoding: 'utf-8', timeout: 30000 }
    );
    assert.ok(out.includes('PR Review'));
    assert.ok(out.includes('Summary'));
    assert.ok(out.includes('Identified Risks'));
    assert.ok(out.includes('Improvement Suggestions'));
    assert.ok(out.includes('Confidence Score'));
    assert.ok(out.includes('sjkim1127'));
  });

  it('reviews a second real PR (Test PR 2)', () => {
    const out = execSync(
      'node ' + CLI + ' --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2233',
      { encoding: 'utf-8', timeout: 30000 }
    );
    assert.ok(out.includes('PR Review'));
    assert.ok(out.includes('Summary'));
    assert.ok(out.includes('Confidence Score'));
  });

  it('--json flag outputs valid JSON', () => {
    const out = execSync(
      'node ' + CLI + ' --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2234 --json',
      { encoding: 'utf-8', timeout: 30000 }
    );
    const parsed = JSON.parse(out);
    assert.equal(parsed.tool, 'claude-review');
    assert.ok(parsed.stats);
    assert.ok(parsed.analysis);
    assert.ok(['Low', 'Medium', 'High'].includes(parsed.analysis.confidence));
  });

});