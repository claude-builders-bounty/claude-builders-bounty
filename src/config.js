import dotenv from "dotenv";
dotenv.config();

export const config = {
  anthropicApiKey: process.env.ANTHROPIC_API_KEY,
  githubToken: process.env.GITHUB_TOKEN,
  apiBase: "https://api.anthropic.com",
  model: "claude-sonnet-4-20250514",
  maxTokens: 4096,
};

export function validateConfig() {
  if (!config.anthropicApiKey) {
    throw new Error(
      "ANTHROPIC_API_KEY is required. Set it in your environment or .env file."
    );
  }
  if (!config.githubToken) {
    throw new Error(
      "GITHUB_TOKEN is required. Set it in your environment or .env file."
    );
  }
}
