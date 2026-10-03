import { config } from "./config.js";
import { buildReviewPrompt } from "./prompts.js";

const API_URL = `${config.apiBase}/v1/messages`;

export async function reviewPr(prInfo, diff, files) {
  const prompt = buildReviewPrompt(prInfo, diff, files);

  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${config.anthropicApiKey}`,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: config.model,
      max_tokens: config.maxTokens,
      messages: [{ role: "user", content: prompt }],
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${text}`);
  }

  const data = await res.json();
  const content = data.content?.[0]?.text?.trim();
  if (!content) {
    throw new Error("No review content returned from Claude.");
  }
  return content;
}
