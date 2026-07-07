#!/usr/bin/env node

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { generateReview } from "./lib/anthropic.mjs";
import { getHelpText, parseArgs } from "./lib/args.mjs";
import { buildFrontMatter, buildReviewPrompt, validateReviewMarkdown } from "./lib/format.mjs";
import { clipDiff, getPullRequestContext } from "./lib/github.mjs";

async function main() {
  let args;

  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.error(error.message);
    console.error("");
    console.error(getHelpText());
    process.exitCode = 1;
    return;
  }

  if (args.help) {
    process.stdout.write(getHelpText());
    return;
  }

  const context = await getPullRequestContext(args.pr);
  const clipped = clipDiff(context.diff, args.maxDiffChars);
  const prompt = buildReviewPrompt({
    ...context,
    diff: clipped.diff
  });

  if (args.promptOnly) {
    process.stdout.write(prompt);
    return;
  }

  const generated = await generateReview(prompt);
  const markdown = generated.startsWith("## PR Review")
    ? generated
    : `${buildFrontMatter(context)}${generated.startsWith("\n") ? "" : "\n"}${generated}`;

  if (!validateReviewMarkdown(markdown)) {
    throw new Error("Claude response did not match the required Markdown structure.");
  }

  if (args.out) {
    const target = path.resolve(process.cwd(), args.out);
    await mkdir(path.dirname(target), { recursive: true });
    await writeFile(target, `${markdown}\n`, "utf8");
    process.stdout.write(`Saved review to ${target}\n`);
    return;
  }

  process.stdout.write(`${markdown}\n`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
