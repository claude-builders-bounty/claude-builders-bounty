import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_MODEL = "claude-sonnet-4-20250514";
const ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages";

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));
const promptPath = path.resolve(currentDirectory, "..", "..", ".claude", "agents", "pr-reviewer.md");

export async function readSystemPrompt() {
  return readFile(promptPath, "utf8");
}

export async function generateReview(prompt, options = {}) {
  const apiKey = options.apiKey ?? process.env.ANTHROPIC_API_KEY;
  const model = options.model ?? process.env.ANTHROPIC_MODEL ?? DEFAULT_MODEL;
  const system = options.systemPrompt ?? await readSystemPrompt();

  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY is required unless --prompt-only is used.");
  }

  const response = await fetch(ANTHROPIC_API_URL, {
    method: "POST",
    headers: {
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
      "x-api-key": apiKey
    },
    body: JSON.stringify({
      max_tokens: 1200,
      model,
      system,
      messages: [
        {
          role: "user",
          content: [
            {
              type: "text",
              text: prompt
            }
          ]
        }
      ]
    })
  });

  if (!response.ok) {
    throw new Error(`Anthropic request failed (${response.status}): ${await response.text()}`);
  }

  const payload = await response.json();
  const textBlocks = Array.isArray(payload.content)
    ? payload.content.filter((entry) => entry.type === "text").map((entry) => entry.text)
    : [];

  return textBlocks.join("\n").trim();
}
