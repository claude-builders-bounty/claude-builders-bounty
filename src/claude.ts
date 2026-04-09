import Anthropic from "@anthropic-ai/sdk";
import { DiffResult, ReviewResult } from "./types";

const SYSTEM_PROMPT = `You are an expert code reviewer. Analyze the provided PR diff and return a structured review.

Output ONLY valid JSON with this exact schema:
{
  "summary": "2-3 sentence summary of what this PR does",
  "risks": ["list", "of", "identified", "risks"],
  "suggestions": ["list", "of", "improvement", "suggestions"],
  "confidence": "Low" | "Medium" | "High"
}

Review guidelines:
- Focus on real issues: bugs, security risks, performance problems, maintainability
- Be constructive and specific
- If the change is trivial (e.g., typo fix), say so
- If the diff is empty or too large, note that in the summary
- Confidence should reflect how well you can assess the changes`;

export async function analyzeWithClaude(
  diff: DiffResult,
  model?: string
): Promise<ReviewResult> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error(
      "ANTHROPIC_API_KEY not set. Use template mode or set the environment variable."
    );
  }

  const anthropic = new Anthropic({ apiKey });
  const selectedModel = model || "claude-sonnet-4-20250514";

  console.log(`🤖 Analyzing with ${selectedModel}...`);

  const maxDiffLength = 100000;
  const diffContent =
    diff.diff.length > maxDiffLength
      ? diff.diff.slice(0, maxDiffLength) + "\n\n[... diff truncated due to size ...]"
      : diff.diff;

  const message = await anthropic.messages.create({
    model: selectedModel,
    max_tokens: 2048,
    system: SYSTEM_PROMPT,
    messages: [
      {
        role: "user",
        content: `PR Title: ${diff.prInfo.title}\nAuthor: ${diff.prInfo.author}\nFiles changed: ${diff.prInfo.changedFiles}\nAdditions: +${diff.prInfo.additions} | Deletions: -${diff.prInfo.deletions}\n\nDiff:\n${diffContent}`,
      },
    ],
  });

  const textContent = message.content.filter(
    (block) => block.type === "text"
  ) as Array<{ type: "text"; text: string }>;
  const text = textContent.map((block) => block.text).join("\n");

  // Extract JSON from response (may be wrapped in code blocks)
  const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  const jsonStr = jsonMatch ? jsonMatch[1].trim() : text.trim();

  try {
    const parsed = JSON.parse(jsonStr) as ReviewResult;
    return { ...parsed, rawResponse: text };
  } catch {
    // Fallback: try to parse without code block markers
    return {
      summary: extractSummary(text),
      risks: extractList(text, "risks"),
      suggestions: extractList(text, "suggestions"),
      confidence: extractConfidence(text),
      rawResponse: text,
    };
  }
}

function extractSummary(text: string): string {
  const summaryMatch = text.match(/summary["\s:]*(.*?)(?=\n\n|$)/i);
  return summaryMatch
    ? summaryMatch[1].replace(/^["\s-]+/, "").trim()
    : text.slice(0, 200);
}

function extractList(text: string, key: string): string[] {
  const sectionRegex = new RegExp(`${key}[\\s:]*\\n([\\s\\S]*?)(?=\\n\\n|$)`, "i");
  const match = text.match(sectionRegex);
  if (!match) return [];
  return match[1]
    .split("\n")
    .map((line) => line.replace(/^[\s-•*]+/, "").trim())
    .filter(Boolean);
}

function extractConfidence(text: string): "Low" | "Medium" | "High" {
  const match = text.match(/confidence["\s:]*\b(Low|Medium|High)\b/i);
  if (!match) return "Medium";
  return match[1] as "Low" | "Medium" | "High";
}
