'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert');
const { buildPrompt, formatReviewComment, validateReview } = require('../src/reviewer');

describe('buildPrompt', () => {
  const prData = {
    title: 'Add user auth',
    author: 'dev123',
    head: 'feature/auth',
    base: 'main',
    filesChanged: 5,
    additions: 200,
    deletions: 30,
    body: 'Implements JWT-based authentication',
    diff: 'diff --git a/auth.js b/auth.js\n+const jwt = require("jsonwebtoken");',
  };

  it('includes PR metadata in prompt', () => {
    const prompt = buildPrompt(prData);
    assert.ok(prompt.includes('Add user auth'));
    assert.ok(prompt.includes('dev123'));
    assert.ok(prompt.includes('feature/auth'));
    assert.ok(prompt.includes('main'));
    assert.ok(prompt.includes('+200'));
    assert.ok(prompt.includes('-30'));
  });

  it('includes PR description', () => {
    const prompt = buildPrompt(prData);
    assert.ok(prompt.includes('JWT-based authentication'));
  });

  it('includes the diff', () => {
    const prompt = buildPrompt(prData);
    assert.ok(prompt.includes('jsonwebtoken'));
  });

  it('truncates very long diffs', () => {
    const longData = { ...prData, diff: 'x'.repeat(60000) };
    const prompt = buildPrompt(longData);
    assert.ok(prompt.includes('[... diff truncated at 50000 chars ...]'));
    assert.ok(prompt.length < 60000);
  });

  it('handles empty PR body', () => {
    const noBody = { ...prData, body: '' };
    const prompt = buildPrompt(noBody);
    assert.ok(prompt.includes('(no description provided)'));
  });
});

describe('validateReview', () => {
  it('validates a correct review', () => {
    const review = `## Summary
This PR adds auth.

## Risks
- Token expiry not handled

## Suggestions
- Add refresh tokens

## Confidence
**High**`;
    const result = validateReview(review);
    assert.strictEqual(result.valid, true);
    assert.deepStrictEqual(result.missing, []);
  });

  it('detects missing sections', () => {
    const review = `## Summary
This PR adds auth.

## Confidence
**High**`;
    const result = validateReview(review);
    assert.strictEqual(result.valid, false);
    assert.ok(result.missing.includes('## Risks'));
    assert.ok(result.missing.includes('## Suggestions'));
  });

  it('rejects empty review', () => {
    const result = validateReview('');
    assert.strictEqual(result.valid, false);
    assert.strictEqual(result.missing.length, 4);
  });
});

describe('formatReviewComment', () => {
  it('wraps review in a formatted comment', () => {
    const review = '## Summary\nGreat PR.';
    const prData = { number: 42, title: 'Fix bug' };
    const comment = formatReviewComment(review, prData);
    assert.ok(comment.includes('# 🤖 Claude Code Review'));
    assert.ok(comment.includes('PR #42'));
    assert.ok(comment.includes('Fix bug'));
    assert.ok(comment.includes('Great PR.'));
    assert.ok(comment.includes('claude-review'));
  });
});
