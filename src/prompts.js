export function buildReviewPrompt(prInfo, diff, files) {
  const summaryBlock = prInfo.title
    ? `Title: ${prInfo.title}\n`
    : "";
  const descriptionBlock = prInfo.body
    ? `Description:\n${prInfo.body}\n\n`
    : "";
  const filesBlock = files
    ? `Modified files:\n${files
        .map((f) => `- ${f.filename} (${f.changes} lines changed)`)
        .join("\n")}\n\n`
    : "";

  const truncatedDiff =
    diff.length > 25000 ? diff.slice(0, 25000) + "\n\n... [diff truncated] ..." : diff;

  return `You are an expert code reviewer. Analyze the following GitHub pull request and produce a structured review.

## PR Information
${summaryBlock}${descriptionBlock}${filesBlock}
## PR Diff
\`\`\`diff
${truncatedDiff}
\`\`\`

Please produce a review in the following exact Markdown format:

## Summary
[2-3 sentences summarizing the purpose and scope of the changes]

## Identified Risks
- [risk 1]
- [risk 2]
- [if no risks identified: None detected]

## Improvement Suggestions
- [suggestion 1]
- [suggestion 2]
- [if no suggestions: No critical improvements needed]

## Confidence Score
[Low / Medium / High]

Only output the structured review. Do not include any preamble or explanation outside the format above.`;
}
