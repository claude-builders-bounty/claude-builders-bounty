/**
 * Analyze a PR diff using the Anthropic Claude API.
 * Returns structured review data.
 */

import Anthropic from "@anthropic-ai/sdk";

const SYSTEM_PROMPT = `You are an expert code reviewer. You will receive a GitHub Pull Request diff along with its metadata. Analyze the changes and produce a structured review.

Your review MUST follow this exact JSON structure:
{
  "summary": "A concise 2-3 sentence summary of what this PR does and its overall approach.",
  "risks": [
    "Each risk as a separate string item",
    "Focus on: bugs, security issues, performance problems, breaking changes, missing edge cases"
  ],
  "suggestions": [
    "Each actionable improvement suggestion as a separate string item",
    "Be specific: mention file names, line ranges, and concrete alternatives"
  ],
  "confidence": "Low | Medium | High",
  "confidence_reasoning": "Brief explanation of your confidence level"
}

Rules:
- If the diff is too large or truncated, note this in the summary and lower your confidence.
- If there are no risks, return an empty array for "risks".
- If there are no suggestions, return an empty array for "suggestions".
- Be constructive, not pedantic. Focus on meaningful issues.
- Always return valid JSON, nothing else.`;

const MAX_DIFF_CHARS = 24000;

/**
 * Analyze a PR diff with Claude.
 * @param {Object} params
 * @param {string} params.diff - The unified diff content
 * @param {Object} params.meta - PR metadata (title, body, etc.)
 * @param {string} [params.apiKey] - Anthropic API key (falls back to ANTHROPIC_API_KEY env)
 * @returns {Promise<Object>} Structured review data
 */
export async function analyzeDiff({ diff, meta, apiKey }) {
  const client = new Anthropic({
    apiKey: apiKey || process.env.ANTHROPIC_API_KEY,
  });

  let truncated = false;
  let diffContent = diff;
  if (diff.length > MAX_DIFF_CHARS) {
    diffContent = diff.slice(0, MAX_DIFF_CHARS);
    truncated = true;
  }

  const userMessage = `## Pull Request Metadata
- **Title:** ${meta.title}
- **Author:** ${meta.author}
- **Branch:** ${meta.head} → ${meta.base}
- **Description:** ${meta.body}
- **Stats:** +${meta.additions} / -${meta.deletions} across ${meta.changedFiles} files
${truncated ? "\n⚠️ **Note:** The diff was truncated (showing first ~24,000 characters of " + diff.length.toLocaleString() + " total).\n" : ""}

## Diff
\`\`\`diff
${diffContent}
\`\`\``;

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 2048,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: userMessage }],
  });

  const text = response.content
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("");

  try {
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in response");
    }
    return JSON.parse(jsonMatch[0]);
  } catch (err) {
    return {
      summary: text.slice(0, 500),
      risks: ["Failed to parse structured response from Claude"],
      suggestions: ["Raw response was returned as summary"],
      confidence: "Low",
      confidence_reasoning: "Response parsing failed",
    };
  }
}
