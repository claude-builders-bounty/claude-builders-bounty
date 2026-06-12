// Wrapper that calls the real-review path so generate-examples.ts can
// branch on ANTHROPIC_API_KEY without duplicating the Anthropic
// client construction in cli.ts.

import type { PullRequest } from "./fetch-pr.js";
import { buildReviewPrompt, parseReviewOutput, type Review } from "./review.js";

export async function realReview(
  context: PullRequest,
  model: string,
): Promise<Review> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY is not set");
  }
  const { default: Anthropic } = await import("@anthropic-ai/sdk");
  const client = new Anthropic({ apiKey });
  const prompt = buildReviewPrompt(context);

  const response = await client.messages.create({
    model,
    max_tokens: 2048,
    system: prompt.system,
    messages: [{ role: "user", content: prompt.user }],
  });

  const text = response.content
    .filter((b): b is { type: "text"; text: string } => b.type === "text")
    .map((b) => b.text)
    .join("");

  const parsed = parseReviewOutput(text, context);
  return { ...parsed, source: { kind: "claude", model } };
}
