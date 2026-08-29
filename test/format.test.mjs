import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeMarkdown, validateReviewMarkdown } from '../src/format.mjs';

const VALID = `## Summary
This changes request parsing. The implementation is generally sound.

## Identified Risks
- [Low] One edge case may be untested.

## Improvement Suggestions
- Add a regression test for the edge case.

## Confidence: High`;

test('valid structured review passes validation', () => {
  const result = validateReviewMarkdown(VALID);
  assert.equal(result.ok, true);
  assert.equal(result.confidence, 'High');
});

test('missing confidence fails validation', () => {
  const result = validateReviewMarkdown(VALID.replace('## Confidence: High', 'Confidence high'));
  assert.equal(result.ok, false);
  assert.match(result.errors.join(' '), /confidence/);
});

test('normalizeMarkdown strips one wrapping markdown code fence', () => {
  assert.equal(normalizeMarkdown(`\`\`\`markdown\n${VALID}\n\`\`\``), VALID);
});
