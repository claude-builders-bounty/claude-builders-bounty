export function buildReviewPrompt(context) {
  const summary = [
    `Repository: ${context.owner}/${context.repo}`,
    `PR: #${context.number}`,
    `Title: ${context.title}`,
    `Author: @${context.author}`,
    `Base branch: ${context.baseRef}`,
    `Head branch: ${context.headRef}`,
    `Changed files: ${context.changedFiles}`,
    `Additions: +${context.additions}`,
    `Deletions: -${context.deletions}`,
    `PR URL: ${context.url}`
  ].join("\n");

  const bodySection = context.body
    ? `\nPR description:\n${context.body}\n`
    : "\nPR description:\n(none)\n";

  return `${summary}${bodySection}
Review the following pull request diff. Return Markdown only.

Required structure:
## PR Review

> **PR**: owner/repo#number
> **Title**: short title
> **Author**: @username

### Summary
Write 2-3 sentences summarizing the change.

### Identified Risks
- Bullet list

### Improvement Suggestions
- Bullet list

### Confidence
Low | Medium | High

Focus on concrete code-review findings. If there are no major issues, say so plainly and keep the suggestions practical.

Diff:
\`\`\`diff
${context.diff}
\`\`\`
`;
}

export function buildFrontMatter(context) {
  return [
    "## PR Review",
    "",
    `> **PR**: ${context.owner}/${context.repo}#${context.number}`,
    `> **Title**: ${context.title}`,
    `> **Author**: @${context.author}`,
    ""
  ].join("\n");
}

export function validateReviewMarkdown(markdown) {
  const requiredPatterns = [
    /^## PR Review$/m,
    /^### Summary$/m,
    /^### Identified Risks$/m,
    /^### Improvement Suggestions$/m,
    /^### Confidence$/m,
    /^(Low|Medium|High)$/m
  ];

  return requiredPatterns.every((pattern) => pattern.test(markdown));
}
