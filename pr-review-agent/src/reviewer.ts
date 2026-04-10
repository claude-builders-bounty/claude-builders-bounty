/**
 * reviewer.ts — Core PR review logic via Claude API
 */

import Anthropic from "@anthropic-ai/sdk";
import { z } from "zod";

const ReviewSchema = z.object({
  summary: z.string().describe("2-3 sentence summary of what changed"),
  risks: z.array(z.string()).describe("List of identified risks or concerns"),
  suggestions: z.array(z.string()).describe("List of improvement suggestions"),
  confidence: z.enum(["Low", "Medium", "High"]).describe("Reviewer confidence level"),
});

const SYSTEM_PROMPT = `You are an expert code reviewer. Analyze the provided PR diff and produce a thorough, constructive code review.

Respond ONLY with a valid JSON object matching this schema:
{
  "summary": "2-3 sentence summary of what changed",
  "risks": ["risk 1", "risk 2", ...],
  "suggestions": ["suggestion 1", "suggestion 2", ...],
  "confidence": "Low" | "Medium" | "High"
}

Guidelines:
- summary: What does this PR do? What is the intent?
- risks: Security vulnerabilities, data loss risks, breaking changes, performance concerns, regression potential
- suggestions: Code quality improvements, missing tests, documentation gaps, better patterns
- confidence: High = you fully understand the code; Low = unfamiliar domain or very complex changes`;

const REVIEW_TEMPLATE = (diff: string): string => `
## PR Diff Review

\`\`\`diff
${diff}
\`\`\`

Please review this PR diff and respond with your analysis as JSON.
`;

export async function reviewPR(
  diff: string,
  opts: { apiKey: string; model?: string }
): Promise<string> {
  const client = new Anthropic({ apiKey: opts.apiKey });

  const response = await client.messages.create({
    model: opts.model || "claude-sonnet-4-20250514",
    max_tokens: 2048,
    system: SYSTEM_PROMPT,
    messages: [
      {
        role: "user",
        content: REVIEW_TEMPLATE(diff),
      },
    ],
  });

  const rawText = response.content
    .filter((block) => block.type === "text")
    .map((block) => (block as { type: "text"; text: string }).text)
    .join("\n")
    .trim();

  let parsed: z.infer<typeof ReviewSchema>;
  try {
    // Try to extract JSON from the response
    const jsonMatch = rawText.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("No JSON found in response");
    parsed = ReviewSchema.parse(JSON.parse(jsonMatch[0]));
  } catch {
    // Fall back to raw text if parsing fails
    return `## Claude Code PR Review\n\n${rawText}\n`;
  }

  const lines: string[] = [
    "## Claude Code PR Review",
    "",
    "### Summary",
    parsed.summary,
    "",
    "### Risks",
  ];

  if (parsed.risks.length === 0) {
    lines.push("- No significant risks identified.");
  } else {
    for (const risk of parsed.risks) {
      lines.push(`- ${risk}`);
    }
  }

  lines.push("", "### Suggestions");

  if (parsed.suggestions.length === 0) {
    lines.push("- Code looks good. No immediate suggestions.");
  } else {
    for (const suggestion of parsed.suggestions) {
      lines.push(`- ${suggestion}`);
    }
  }

  lines.push("", `**Confidence Score:** ${parsed.confidence}`);

  return lines.join("\n");
}
