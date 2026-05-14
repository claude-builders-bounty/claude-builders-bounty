#!/usr/bin/env node
/**
 * Weekly Dev Summary Generator — standalone CLI
 * No n8n required. Runs directly with Node.js.
 *
 * Usage:
 *   ANTHROPIC_API_KEY=sk-... GITHUB_TOKEN=ghp_... GITHUB_REPO=owner/repo node generate.js
 *
 * Optional env vars:
 *   SINCE_DAYS   — how many days back to fetch (default: 7)
 *   OUTPUT_FILE  — save summary to file instead of stdout
 */

const https = require("https");

const {
  ANTHROPIC_API_KEY,
  GITHUB_TOKEN,
  GITHUB_REPO,
  SINCE_DAYS = "7",
  OUTPUT_FILE,
} = process.env;

if (!ANTHROPIC_API_KEY || !GITHUB_TOKEN || !GITHUB_REPO) {
  console.error(
    "Error: ANTHROPIC_API_KEY, GITHUB_TOKEN, and GITHUB_REPO are required."
  );
  process.exit(1);
}

const [owner, repo] = GITHUB_REPO.split("/");
const since = new Date(
  Date.now() - parseInt(SINCE_DAYS) * 24 * 60 * 60 * 1000
).toISOString();

function githubGet(path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: "api.github.com",
      path,
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        "User-Agent": "weekly-dev-summary",
        Accept: "application/vnd.github.v3+json",
      },
    };
    const req = https.get(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => resolve(JSON.parse(data)));
    });
    req.on("error", reject);
    req.setTimeout(30000, () => { req.destroy(); reject(new Error("Timeout")); });
  });
}

function claudeComplete(prompt) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1024,
      messages: [{ role: "user", content: prompt }],
    });
    const options = {
      hostname: "api.anthropic.com",
      path: "/v1/messages",
      method: "POST",
      headers: {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "content-length": Buffer.byteLength(body),
      },
    };
    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        const parsed = JSON.parse(data);
        resolve(parsed.content?.[0]?.text || "");
      });
    });
    req.on("error", reject);
    req.setTimeout(30000, () => { req.destroy(); reject(new Error("Timeout")); });
    req.write(body);
    req.end();
  });
}

async function main() {
  console.error(`Fetching activity for ${GITHUB_REPO} since ${since}...`);

  const [commits, prs] = await Promise.all([
    githubGet(`/repos/${owner}/${repo}/commits?since=${since}&per_page=50`),
    githubGet(
      `/repos/${owner}/${repo}/pulls?state=all&sort=updated&direction=desc&per_page=30`
    ),
  ]);

  const recentPRs = prs.filter((pr) => new Date(pr.updated_at) >= new Date(since));

  const commitList = Array.isArray(commits)
    ? commits.map((c) => `- ${c.commit.message.split("\n")[0]} (@${c.author?.login || "unknown"})`).join("\n")
    : "No commits found.";

  const prList = recentPRs
    .map((pr) => `- [${pr.state.toUpperCase()}] ${pr.title} (#${pr.number}) by @${pr.user.login}`)
    .join("\n") || "No PRs found.";

  const prompt = `You are a technical writer. Generate a concise weekly development summary for the GitHub repository ${GITHUB_REPO}.

## Commits (last ${SINCE_DAYS} days)
${commitList}

## Pull Requests (last ${SINCE_DAYS} days)
${prList}

Write a professional Markdown summary with:
1. A one-paragraph executive overview
2. Key highlights (bullet points)
3. Notable contributors
4. Any patterns or trends you notice

Keep it under 400 words. Use ## headers.`;

  console.error("Generating summary with Claude...");
  const summary = await claudeComplete(prompt);

  const output = `# Weekly Dev Summary — ${GITHUB_REPO}\n_Generated: ${new Date().toUTCString()}_\n\n${summary}`;

  if (OUTPUT_FILE) {
    require("fs").writeFileSync(OUTPUT_FILE, output);
    console.error(`Saved to ${OUTPUT_FILE}`);
  } else {
    console.log(output);
  }
}

main().catch((err) => {
  console.error("Fatal:", err.message);
  process.exit(1);
});
