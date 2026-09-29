#!/usr/bin/env node
import { fetchPR } from "./github";
import { analyzePR, formatMarkdown } from "./review";
import * as path from "path";

async function main() {
  const args = process.argv.slice(2);
  const prUrl = args[0];
  const token = process.env.GITHUB_TOKEN;

  if (!prUrl) {
    console.error("Usage: claude-review <pr-url> [--format=markdown]");
    console.error("Example: claude-review https://github.com/owner/repo/pull/123");
    process.exit(1);
  }

  try {
    console.error("Fetching PR data...");
    const pr = await fetchPR(prUrl, token);

    console.error("Analyzing diff...");
    const review = analyzePR(pr);

    const format = args.includes("--format=markdown") ? "markdown" : "markdown";
    if (format === "markdown") {
      console.log(formatMarkdown(pr, review));
    }
  } catch (err) {
    console.error(`Error: ${err instanceof Error ? err.message : err}`);
    process.exit(1);
  }
}

main();