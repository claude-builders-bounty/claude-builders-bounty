#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const {
  buildReviewFromPullRequest,
  formatReviewMarkdown,
  parseArgs,
  usage
} = require('../src/claudeReview');

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    process.stdout.write(usage());
    return;
  }

  const review = await buildReviewFromPullRequest(args);
  const markdown = formatReviewMarkdown(review);

  if (args.output) {
    const outputPath = path.resolve(args.output);
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, markdown);
  } else {
    process.stdout.write(markdown);
    if (!markdown.endsWith('\n')) {
      process.stdout.write('\n');
    }
  }
}

main().catch((error) => {
  process.stderr.write(`claude-review: ${error.message}\n`);
  if (process.env.DEBUG) {
    process.stderr.write(`${error.stack}\n`);
  }
  process.exitCode = 1;
});
