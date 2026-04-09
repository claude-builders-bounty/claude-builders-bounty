import { DiffResult, ReviewResult } from "./types";

export function formatReviewMarkdown(
  diff: DiffResult,
  review: ReviewResult
): string {
  const { prInfo } = diff;

  const lines: string[] = [
    `## 📋 PR #${prInfo.number}: ${prInfo.title}`,
    "",
    `**Author:** ${prInfo.author}  `,
    `**Changes:** +${prInfo.additions} -${prInfo.deletions} across ${prInfo.changedFiles} file(s)`,
    `**Diff size:** ${diff.diffSizeKB} KB`,
    "",
    "---",
    "",
    "## Summary",
    "",
    review.summary,
    "",
    "---",
    "",
    "## 🔴 Risks",
    "",
    ...review.risks.map((r) => `- ${r}`),
    "",
    "---",
    "",
    "## 💡 Suggestions",
    "",
    ...review.suggestions.map((s) => `- ${s}`),
    "",
    "---",
    "",
    "## Confidence",
    "",
    `${review.confidence === "High" ? "🟢" : review.confidence === "Medium" ? "🟡" : "🔴"} **${review.confidence}**`,
    "",
  ];

  return lines.join("\n");
}

export function formatConsoleSummary(diff: DiffResult): string {
  const { prInfo } = diff;
  return [
    `📋 PR #${prInfo.number}: ${prInfo.title}`,
    `Author: ${prInfo.author}`,
    `Changes: +${prInfo.additions} -${prInfo.deletions}`,
  ].join("\n");
}
