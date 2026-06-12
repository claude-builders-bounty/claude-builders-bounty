import type { Review } from "./review.js";

export function formatMarkdown(review: Review): string {
  const lines: string[] = [];
  lines.push("## Summary");
  lines.push("");
  lines.push(review.summary || "(no summary)");
  lines.push("");
  lines.push("## Risks");
  lines.push("");
  if (review.risks.length === 0) {
    lines.push("- None identified.");
  } else {
    for (const r of review.risks) lines.push(`- ${r}`);
  }
  lines.push("");
  lines.push("## Improvements");
  lines.push("");
  if (review.improvements.length === 0) {
    lines.push("- None identified.");
  } else {
    for (const r of review.improvements) lines.push(`- ${r}`);
  }
  lines.push("");
  lines.push("## Confidence");
  lines.push("");
  lines.push(`${review.confidence} — ${confidenceRationale(review)}`);
  lines.push("");
  return lines.join("\n");
}

function confidenceRationale(review: Review): string {
  if (review.source.kind === "mock") {
    return "Heuristic mock reviewer; treat as a starting point, not a final review.";
  }
  const loc = review.context.diffLines;
  if (loc < 50) return "Small diff, easy to reason about end-to-end.";
  if (loc < 500) return "Medium-sized diff; review covered the change but not adjacent code.";
  return "Large diff; reviewer may have missed context outside the changed files.";
}

export function formatJson(review: Review): string {
  return JSON.stringify(review, null, 2) + "\n";
}
