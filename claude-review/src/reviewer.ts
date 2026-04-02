import Anthropic from "@anthropic-ai/sdk";
import { PRInfo } from "./github.js";

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

export interface ReviewOutput {
  summary: string;
  risks: string[];
  suggestions: string[];
  confidence: "Low" | "Medium" | "High";
}

function truncateDiff(diff: string, maxLength: number = 80000): string {
  if (diff.length <= maxLength) return diff;
  return diff.slice(0, maxLength) + "\n\n[... Diff truncated due to length ...]";
}

export async function reviewPR(prInfo: PRInfo): Promise<ReviewOutput> {
  const truncatedDiff = truncateDiff(prInfo.diff);
  
  const prompt = `You are an expert code reviewer. Analyze the following Pull Request and provide a structured review.

## PR Details
- **Title:** ${prInfo.title}
- **Author:** ${prInfo.author}
- **Base Branch:** ${prInfo.baseBranch}
- **Head Branch:** ${prInfo.headBranch}
- **Files Changed:** ${prInfo.files.join(", ")}
- **Additions:** +${prInfo.additions} | **Deletions:** -${prInfo.deletions}

## PR Description
${prInfo.body || "(No description provided)"}

## Diff
\`\`\`diff
${truncatedDiff}
\`\`\`

## Your Task
Provide a structured code review with:

1. **Summary** (2-3 sentences): Briefly describe what this PR does and its overall purpose
2. **Identified Risks** (bullet list): Security issues, potential bugs, breaking changes, performance concerns
3. **Improvement Suggestions** (bullet list): Code quality improvements, best practices, optimizations
4. **Confidence Score**: Rate your confidence in this review as Low, Medium, or High

Be thorough but constructive. Focus on actionable feedback.

## Output Format
Provide your response in this exact Markdown format:

### Summary
[Your 2-3 sentence summary here]

### Identified Risks
- [Risk 1]
- [Risk 2]
- [Risk 3]
...

### Improvement Suggestions
- [Suggestion 1]
- [Suggestion 2]
- [Suggestion 3]
...

### Confidence Score
[Low | Medium | High]`;

  const response = await anthropic.messages.create({
    model: "claude-opus-4-20250514",
    max_tokens: 4096,
    messages: [
      {
        role: "user",
        content: prompt
      }
    ]
  });

  const content = response.content[0];
  if (content.type !== "text") {
    throw new Error("Unexpected response type from Anthropic");
  }

  return parseReviewResponse(content.text);
}

function parseReviewResponse(text: string): ReviewOutput {
  const lines = text.split("\n");
  
  let section = "";
  const summary: string[] = [];
  const risks: string[] = [];
  const suggestions: string[] = [];
  let confidence: "Low" | "Medium" | "High" = "Medium";

  for (const line of lines) {
    const trimmed = line.trim();
    
    if (trimmed.startsWith("### Summary") || trimmed === "Summary") {
      section = "summary";
      continue;
    } else if (trimmed.startsWith("### Identified Risks") || trimmed === "Identified Risks") {
      section = "risks";
      continue;
    } else if (trimmed.startsWith("### Improvement Suggestions") || trimmed === "Improvement Suggestions") {
      section = "suggestions";
      continue;
    } else if (trimmed.startsWith("### Confidence Score") || trimmed === "Confidence Score") {
      section = "confidence";
      continue;
    }

    if (trimmed.startsWith("### ")) {
      continue;
    }

    const cleanedLine = trimmed.replace(/^[-*•]\s*/, "").replace(/^\d+\.\s*/, "");
    
    if (section === "summary" && cleanedLine) {
      summary.push(cleanedLine);
    } else if (section === "risks" && cleanedLine) {
      risks.push(cleanedLine);
    } else if (section === "suggestions" && cleanedLine) {
      suggestions.push(cleanedLine);
    } else if (section === "confidence" && cleanedLine) {
      if (cleanedLine.toLowerCase().includes("low")) confidence = "Low";
      else if (cleanedLine.toLowerCase().includes("high")) confidence = "High";
      else confidence = "Medium";
    }
  }

  return {
    summary: summary.join(" ") || "Unable to generate summary.",
    risks,
    suggestions,
    confidence
  };
}

export function formatReviewAsMarkdown(prInfo: PRInfo, review: ReviewOutput): string {
  return `## 🔍 Claude PR Review

**PR:** [#${prInfo.prNumber}](https://github.com/${prInfo.owner}/${prInfo.repo}/pull/${prInfo.prNumber}) **${prInfo.title}**
**Author:** @${prInfo.author}
**Files:** ${prInfo.files.length} | **+${prInfo.additions}** / **-${prInfo.deletions}**

---

### Summary
${review.summary}

### Identified Risks
${review.risks.length > 0 ? review.risks.map(r => `- ${r}`).join("\n") : "- No significant risks identified"}

### Improvement Suggestions
${review.suggestions.length > 0 ? review.suggestions.map(s => `- ${s}`).join("\n") : "- No suggestions at this time"}

### Confidence Score
${review.confidence === "High" ? "🟢 High" : review.confidence === "Medium" ? "🟡 Medium" : "🔴 Low"}

---

*Reviewed by [Claude](https://claude.ai) via claude-review • [Source](https://github.com/claude-builders-bounty/claude-builders-bounty)*`;
}
