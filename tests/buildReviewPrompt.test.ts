/**
 * 测试 review prompt 构建。
 * 确保 prompt 包含了所有需要的信息段。
 */
import { describe, it, expect } from 'vitest';

// Simulate the prompt builder (extracted for testability)
function buildReviewPrompt(
  prInfo: { title: string; description: string; changedFiles: number; additions: number; deletions: number },
  diff: string,
): string {
  return `You are an expert code reviewer. Review the following Pull Request and produce a structured Markdown analysis.

## PR Information
- **Title:** ${prInfo.title}
- **Description:** ${prInfo.description}
- **Files changed:** ${prInfo.changedFiles}
- **Additions:** ${prInfo.additions}
- **Deletions:** ${prInfo.deletions}

## Diff
\`\`\`diff
${diff.slice(0, 80000)}
\`\`\`

## Output Format

Return ONLY a structured Markdown review with these exact sections:

### Summary
(2-3 sentences summarizing what the PR does)

### Identified Risks
- Risk 1: (description)
- Risk 2: (description)
...

### Improvement Suggestions
- Suggestion 1: (actionable recommendation)
- Suggestion 2: (actionable recommendation)
...

### Confidence Score
**Score:** Low / Medium / High
(Brief justification for the score)
`;
}

describe('buildReviewPrompt', () => {
  const prInfo = {
    title: 'Add user login feature',
    description: 'Implements JWT-based login with refresh tokens',
    changedFiles: 5,
    additions: 200,
    deletions: 20,
  };

  it('includes PR title in prompt', () => {
    const prompt = buildReviewPrompt(prInfo, 'diff content');
    expect(prompt).toContain('Add user login feature');
  });

  it('includes PR description', () => {
    const prompt = buildReviewPrompt(prInfo, 'diff content');
    expect(prompt).toContain('JWT-based login');
  });

  it('includes file change stats', () => {
    const prompt = buildReviewPrompt(prInfo, 'diff content');
    expect(prompt).toContain('5');
    expect(prompt).toContain('200');
    expect(prompt).toContain('20');
  });

  it('includes diff content', () => {
    const prompt = buildReviewPrompt(prInfo, 'some-unique-diff-content-here');
    expect(prompt).toContain('some-unique-diff-content-here');
  });

  it('includes output format sections', () => {
    const prompt = buildReviewPrompt(prInfo, 'diff');
    expect(prompt).toContain('### Summary');
    expect(prompt).toContain('### Identified Risks');
    expect(prompt).toContain('### Improvement Suggestions');
    expect(prompt).toContain('### Confidence Score');
  });

  it('truncates diff longer than 80000 chars', () => {
    const longDiff = 'a'.repeat(100000);
    const prompt = buildReviewPrompt(prInfo, longDiff);
    // Should include exactly 80000 chars of diff
    expect(prompt).toContain('a'.repeat(80000));
    // Should NOT include the remaining 20000
    const diffSection = prompt.split('```diff')[1]?.split('```')[0] ?? '';
    // Allow up to 80002 for trailing newline chars
    expect(diffSection.length).toBeLessThanOrEqual(80002);
  });
});
