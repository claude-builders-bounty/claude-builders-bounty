#!/usr/bin/env node
import { fetchPR } from "./github";
import { reviewPR, formatMarkdown } from "./review";
import { Octokit } from "@octokit/rest";

async function main() {
  const args = process.argv.slice(2);
  let prUrl: string | undefined;

  // Parse flags
  let shouldPost = false;
  let useHeuristic = false;
  let model = "claude-sonnet-4-20250514";
  let baseUrl = process.env.ANTHROPIC_BASE_URL;
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith("--pr=")) prUrl = arg.slice(5);
    else if (arg === "--pr" && i < args.length - 1) prUrl = args[i + 1];
    else if (arg.startsWith("http")) prUrl = arg;
    else if (arg === "--post") shouldPost = true;
    else if (arg === "--heuristic") useHeuristic = true;
    else if (arg.startsWith("--model=")) model = arg.slice(8);
    else if (arg.startsWith("--base-url=")) baseUrl = arg.slice(11);
  }

  if (!prUrl) {
    console.error("Usage: claude-review --pr=<url> [options]");
    console.error("");
    console.error("Options:");
    console.error("  --post            Post the review as a PR comment");
    console.error("  --heuristic       Skip Claude API, use heuristic analysis only");
    console.error("  --model=<id>      Claude model (default: claude-sonnet-4-20250514)");
  console.error("  --base-url=<url>  Custom API base (or env ANTHROPIC_BASE_URL)");
    console.error("");
    console.error("Env:");
    console.error("  GITHUB_TOKEN          Required for --post or for private PRs");
    console.error("  ANTHROPIC_API_KEY     Required unless --heuristic is set");
  console.error("  ANTHROPIC_BASE_URL     Optional custom endpoint (e.g. LM Studio http://localhost:1234)");
    console.error("");
    console.error("Examples:");
    console.error("  claude-review --pr=https://github.com/owner/repo/pull/123");
    console.error("  claude-review --pr=https://github.com/owner/repo/pull/123 --post");
    console.error("  claude-review --pr=https://github.com/owner/repo/pull/123 --heuristic");
    process.exit(1);
  }

  const ghToken = process.env.GITHUB_TOKEN;
  const anthropicKey = process.env.ANTHROPIC_API_KEY;

  try {
    console.error("Fetching PR data...");
    const pr = await fetchPR(prUrl, ghToken);

    const mode = useHeuristic || !anthropicKey ? "heuristic" : `Claude (${model})`;
    console.error(`Analyzing with ${mode}...`);
    const review = await reviewPR(pr, { apiKey: anthropicKey, model, useHeuristic, baseUrl });

    const md = formatMarkdown(pr, review);
    console.log(md);

    if (shouldPost) {
      if (!ghToken) {
        console.error("\nError: --post requires GITHUB_TOKEN");
        process.exit(1);
      }
      console.error("\nPosting review to PR...");
      const octokit = new Octokit({ auth: ghToken });
      await octokit.rest.issues.createComment({
        owner: pr.owner,
        repo: pr.repo,
        issue_number: pr.prNumber,
        body: md,
      });
      console.error(`✅ Posted to https://github.com/${pr.owner}/${pr.repo}/pull/${pr.prNumber}`);
    }
  } catch (err) {
    console.error(`Error: ${err instanceof Error ? err.message : err}`);
    process.exit(1);
  }
}

main();
