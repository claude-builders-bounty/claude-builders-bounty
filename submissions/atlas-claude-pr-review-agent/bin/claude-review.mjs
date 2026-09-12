#!/usr/bin/env node
import { writeFile } from "node:fs/promises";
import { fetchPullRequest } from "../src/github.mjs";
import { buildReview } from "../src/review.mjs";

const args = parseArgs(process.argv.slice(2));

if (!args.pr) {
  console.error("Usage: node bin/claude-review.mjs --pr https://github.com/owner/repo/pull/123 [--out review.md]");
  process.exit(2);
}

try {
  const pr = await fetchPullRequest(args.pr);
  const review = buildReview(pr);
  if (args.out) {
    await writeFile(args.out, `${review}\n`, "utf8");
  } else {
    console.log(review);
  }
} catch (error) {
  console.error(`claude-review failed: ${error.message}`);
  process.exit(1);
}

function parseArgs(argv) {
  const result = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--pr") {
      result.pr = argv[i + 1];
      i += 1;
    } else if (argv[i] === "--out") {
      result.out = argv[i + 1];
      i += 1;
    }
  }
  return result;
}
