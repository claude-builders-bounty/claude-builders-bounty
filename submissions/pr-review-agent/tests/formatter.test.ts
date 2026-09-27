import { describe, it, expect } from 'vitest';
import { formatReview } from '../src/formatter.js';
import { PRInfo, PRDiff, ReviewResult } from '../src/types.js';

describe('Formatter', () => {
  const prInfo: PRInfo = {
    owner: 'test', repo: 'repo', number: 1, title: 'Test PR',
    description: '', author: 'dev', baseBranch: 'main', headBranch: 'feat', labels: []
  };
  const prDiff: PRDiff = { files: 1, additions: 10, deletions: 5, rawDiff: '+test' };
  const review: ReviewResult = {
    summary: 'Looks good',
    risks: [{ description: 'Memory leak', severity: 'high' }],
    suggestions: [{ description: 'Use const', priority: 'low' }],
    securityNotes: ['Check inputs'],
    confidence: 'High'
  };

  it('formats to JSON', () => {
    const out = formatReview(prInfo, prDiff, review, { depth: 'standard', format: 'json', postComment: false, verbose: false });
    const parsed = JSON.parse(out);
    expect(parsed.review.summary).toBe('Looks good');
  });

  it('formats to Markdown', () => {
    const out = formatReview(prInfo, prDiff, review, { depth: 'standard', format: 'markdown', postComment: false, verbose: false });
    expect(out).toContain('## 🤖 Claude PR Review');
    expect(out).toContain('Looks good');
    expect(out).toContain('Memory leak');
  });
});
