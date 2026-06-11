#!/usr/bin/env node
import fs from "node:fs/promises";
import { reviewDiff, fetchPullRequestDiff } from "../src/reviewer.js";

const args = parseArgs(process.argv.slice(2));

if (args.help || (!args.pr && !args.diff)) {
  console.log(`Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --diff path/to/pr.diff

Options:
  --json   Emit JSON instead of Markdown
`);
  process.exit(args.help ? 0 : 1);
}

const diff = args.diff
  ? await fs.readFile(args.diff, "utf8")
  : await fetchPullRequestDiff(args.pr);

const review = reviewDiff(diff, { source: args.pr || args.diff });

if (args.json) {
  console.log(JSON.stringify(review, null, 2));
} else {
  console.log(renderMarkdown(review));
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") out.help = true;
    else if (arg === "--json") out.json = true;
    else if (arg === "--pr") out.pr = argv[++i];
    else if (arg === "--diff") out.diff = argv[++i];
  }
  return out;
}

function renderMarkdown(review) {
  const risks = review.risks.map((item) => `- ${item}`).join("\n") || "- No obvious risks found.";
  const suggestions = review.suggestions.map((item) => `- ${item}`).join("\n") || "- No immediate improvements suggested.";
  return `## PR Review

### Summary
${review.summary}

### Identified Risks
${risks}

### Improvement Suggestions
${suggestions}

### Confidence
${review.confidence}
`;
}
