import Anthropic from '@anthropic-ai/sdk';

const SYSTEM_PROMPT = `You are a senior software engineer performing a thorough code review.
Analyze the provided PR diff carefully and return a review using EXACTLY this Markdown structure:

## Summary
(2-3 sentences describing what this PR does and its overall quality)

## Risks
- (List each risk on its own bullet. If none, write "- No significant risks identified.")

## Improvement Suggestions
- (List each suggestion on its own bullet. Include file:line references where possible. If none, write "- Looks good as-is.")

## Confidence Score
(Write exactly one of: Low / Medium / High, followed by one sentence explaining why)

Rules:
- Be specific — reference file names, function names, and line numbers from the diff
- Risks = security issues, breaking changes, missing error handling, race conditions, data loss
- Suggestions = style improvements, missing tests, performance optimizations, better abstractions
- Confidence score reflects how certain you are about your analysis given the diff size/context`;

export async function runReviewAgent(
  diff: string,
  apiKey: string
): Promise<string> {
  const client = new Anthropic({ apiKey });

  const message = await client.messages.create({
    model: 'claude-opus-4-5',
    max_tokens: 2048,
    system: SYSTEM_PROMPT,
    messages: [
      {
        role: 'user',
        content: `Please review this PR diff:\n\n\`\`\`diff\n${diff}\n\`\`\``,
      },
    ],
  });

  const content = message.content[0];
  if (content.type !== 'text') {
    throw new Error('Unexpected response type from Claude API');
  }

  return content.text;
}