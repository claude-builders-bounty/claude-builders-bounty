'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert');
const { execFileSync } = require('child_process');
const path = require('path');

const CLI_PATH = path.join(__dirname, '..', 'bin', 'claude-review.js');

describe('CLI', () => {
  it('prints usage with --help', () => {
    const output = execFileSync('node', [CLI_PATH, '--help'], { encoding: 'utf8' });
    assert.ok(output.includes('claude-review'));
    assert.ok(output.includes('Usage:'));
    assert.ok(output.includes('--pr'));
    assert.ok(output.includes('--post'));
    assert.ok(output.includes('GITHUB_TOKEN'));
  });

  it('prints usage with -h', () => {
    const output = execFileSync('node', [CLI_PATH, '-h'], { encoding: 'utf8' });
    assert.ok(output.includes('Usage:'));
  });

  it('exits with error when no PR URL provided', () => {
    try {
      execFileSync('node', [CLI_PATH], { encoding: 'utf8', stdio: 'pipe' });
      assert.fail('Should have exited with error');
    } catch (err) {
      assert.ok(err.stderr.includes('PR URL is required'));
    }
  });

  it('exits with error for invalid PR URL', () => {
    try {
      execFileSync('node', [CLI_PATH, '--pr', 'not-a-url'], {
        encoding: 'utf8',
        stdio: 'pipe',
      });
      assert.fail('Should have exited with error');
    } catch (err) {
      assert.ok(err.stderr.includes('Invalid GitHub PR URL'));
    }
  });
});
