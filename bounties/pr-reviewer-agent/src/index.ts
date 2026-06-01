#!/usr/bin/env node

import Anthropic from "@anthropic-ai/sdk";

interface PRInfo {
  title: string;
  body: string;
  diff: string;
  files: string[];
}

interface ReviewResult {
  summary: string;
  risks: string[];
  suggestions: string[];
  confidence: "Low" | "Medium" | "High";
}

async function fetchPRInfo(prUrl: string): Promise<PRInfo> {
  const match = prUrl.match(
    /github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/
  );
  if (!match) {
    throw new Error("Invalid GitHub PR URL format");
  }

  const [, owner, repo, prNumber] = match;
  const apiBase = "https://api.github.com";
  const headers: Record<string, string> = {
    Accept: "application/vnd.github.v3+json",
    "User-Agent": "claude-review",
  };

  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `token ${process.env.GITHUB_TOKEN}`;
  }

  const prResponse = await fetch(
    `${apiBase}/repos/${owner}/${repo}/pulls/${prNumber}`,
    { headers }
  );
  if (!prResponse.ok) {
    throw new Error(`Failed to fetch PR: ${prResponse.statusText}`);
  }
  const prData = await prResponse.json();

  const diffResponse = await fetch(
    `${apiBase}/repos/${owner}/${repo}/pulls/${prNumber}`,
    {
      headers: {
        ...headers,
        Accept: "application/vnd.github.v3.diff",
      },
    }
  );
  if (!diffResponse.ok) {
    throw new Error(`Failed to fetch diff: ${diffResponse.statusText}`);
  }
  const diff = await diffResponse.text();

  const filesResponse = await fetch(
    `${apiBase}/repos/${owner}/${repo}/pulls/${prNumber}/files`,
    { headers }
  );
  if (!filesResponse.ok) {
    throw new Error(`Failed to fetch files: ${filesResponse.statusText}`);
  }
  const filesData = await filesResponse.json();
  const files = filesData.map((f: { filename: string }) => f.filename);

  return {
    title: prData.title,
    body: prData.body || "",
    diff: diff.slice(0, 50000),
    files,
  };
}

async function reviewPR(prInfo: PRInfo): Promise<ReviewResult> {
  const client = new Anthropic();

  const prompt = `You are a senior software engineer reviewing a pull request. Analyze the following PR and provide a structured review.

**PR Title:** ${prInfo.title}

**PR Description:**
${prInfo.body || "No description provided"}

**Files Changed:** ${prInfo.files.join(", ")}

**Diff:**
\`\`\`diff
${prInfo.diff}
\`\`\`

Provide your review in the following JSON format:
{
  "summary": "2-3 sentence summary of what this PR does",
  "risks": ["list", "of", "identified", "risks"],
  "suggestions": ["list", "of", "improvement", "suggestions"],
  "confidence": "Low|Medium|High"
}

Confidence levels:
- High: Clear, well-tested changes with minimal risk
- Medium: Reasonable changes but some concerns or missing tests
- Low: Significant concerns, unclear intent, or high-risk changes

Respond ONLY with the JSON object, no other text.`;

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 1024,
    messages: [{ role: "user", content: prompt }],
  });

  const content = message.content[0];
  if (content.type !== "text") {
    throw new Error("Unexpected response type");
  }

  try {
    return JSON.parse(content.text) as ReviewResult;
  } catch {
    throw new Error(`Failed to parse review response: ${content.text}`);
  }
}

function formatReview(review: ReviewResult): string {
  const confidenceEmoji = {
    Low: "🔴",
    Medium: "🟡",
    High: "🟢",
  };

  let output = `## PR Review\n\n`;
  output += `### Summary\n${review.summary}\n\n`;

  if (review.risks.length > 0) {
    output += `### Identified Risks\n`;
    review.risks.forEach((risk) => {
      output += `- ${risk}\n`;
    });
    output += `\n`;
  }

  if (review.suggestions.length > 0) {
    output += `### Suggestions\n`;
    review.suggestions.forEach((suggestion) => {
      output += `- ${suggestion}\n`;
    });
    output += `\n`;
  }

  output += `### Confidence: ${confidenceEmoji[review.confidence]} ${review.confidence}\n`;

  return output;
}

async function main() {
  const args = process.argv.slice(2);
  let prUrl = "";

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--pr" && args[i + 1]) {
      prUrl = args[i + 1];
      break;
    }
    if (args[i].startsWith("https://github.com")) {
      prUrl = args[i];
      break;
    }
  }

  if (!prUrl) {
    console.error("Usage: claude-review --pr <github-pr-url>");
    console.error("Example: claude-review --pr https://github.com/owner/repo/pull/123");
    process.exit(1);
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("Error: ANTHROPIC_API_KEY environment variable is required");
    process.exit(1);
  }

  console.error(`Fetching PR info from ${prUrl}...`);
  const prInfo = await fetchPRInfo(prUrl);

  console.error(`Reviewing PR: ${prInfo.title}`);
  console.error(`Files changed: ${prInfo.files.length}`);

  const review = await reviewPR(prInfo);
  const formatted = formatReview(review);

  console.log(formatted);
}

main().catch((error) => {
  console.error(`Error: ${error.message}`);
  process.exit(1);
});
