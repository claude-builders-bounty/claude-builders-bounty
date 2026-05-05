'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert');
const { parsePrUrl } = require('../src/github');

describe('parsePrUrl', () => {
  it('parses a valid GitHub PR URL', () => {
    const result = parsePrUrl('https://github.com/facebook/react/pull/123');
    assert.deepStrictEqual(result, { owner: 'facebook', repo: 'react', number: 123 });
  });

  it('parses URL with trailing slash or query params', () => {
    const result = parsePrUrl('https://github.com/owner/repo/pull/456/files');
    assert.deepStrictEqual(result, { owner: 'owner', repo: 'repo', number: 456 });
  });

  it('parses URL with hyphenated owner and repo', () => {
    const result = parsePrUrl('https://github.com/my-org/my-repo/pull/789');
    assert.deepStrictEqual(result, { owner: 'my-org', repo: 'my-repo', number: 789 });
  });

  it('throws on invalid URL', () => {
    assert.throws(() => parsePrUrl('https://gitlab.com/owner/repo/pull/1'), /Invalid GitHub PR URL/);
  });

  it('throws on missing PR number', () => {
    assert.throws(() => parsePrUrl('https://github.com/owner/repo/pull/'), /Invalid GitHub PR URL/);
  });

  it('throws on non-PR GitHub URL', () => {
    assert.throws(() => parsePrUrl('https://github.com/owner/repo/issues/42'), /Invalid GitHub PR URL/);
  });
});
