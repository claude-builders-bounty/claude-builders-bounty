#!/usr/bin/env node
import { Command } from "commander";
import { validateConfig, config } from "./config.js";
import {
  parsePrUrl,
  fetchPrInfo,
  fetchPrDiff,
  fetchFiles,
  fetchPrComments,
} from "./github.js";
import { reviewPr } from "./reviewer.js";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = path.join(__dirname, "..", "output");

const program = new Command();

program
  .name("claude-review")
  .description("Claude Code sub-agent that reviews a PR and posts a structured comment")
  .version("1.0.0")
  .argument("<pr-url>", "GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
  .option("-o, --output <file>", "Write review to file instead of stdout")
  .option("--comment-only", "Output only the Markdown review (no extra metadata)")
  .action(async (prUrl, options) => {
    validateConfig();

    const { owner, repo, prNumber } = parsePrUrl(prUrl);
    console.error(`🔍 Reviewing PR #${prNumber} in ${owner}/${repo}...`);

    const [prInfo, diff, files] = await Promise.all([
      fetchPrInfo(owner, repo, prNumber),
      fetchPrDiff(owner, repo, prNumber),
      fetchFiles(owner, repo, prNumber),
    ]);

    console.error(`   Title: ${prInfo.title}`);
    console.error(`   Files changed: ${files.length}`);
    console.error(`   Diff size: ${(diff.length / 1024).toFixed(1)} KB`);

    const review = await reviewPr(prInfo, diff, files);

    const fullOutput = options.commentOnly
      ? review
      : `[Source](https://github.com/${owner}/${repo}/pull/${prNumber})\n\n${review}`;

    if (options.output) {
      const outPath = path.resolve(options.output);
      fs.mkdirSync(path.dirname(outPath), { recursive: true });
      fs.writeFileSync(outPath, fullOutput, "utf-8");
      console.error(`   ✅ Review saved to ${outPath}`);
    } else {
      console.log(fullOutput);
    }
  });

program
  .command("save-output")
  .description("Save the last generated review to the output/ directory with timestamp")
  .argument("<pr-url>", "GitHub PR URL")
  .action(async (prUrl) => {
    validateConfig();
    const { owner, repo, prNumber } = parsePrUrl(prUrl);

    const [prInfo, diff, files] = await Promise.all([
      fetchPrInfo(owner, repo, prNumber),
      fetchPrDiff(owner, repo, prNumber),
      fetchFiles(owner, repo, prNumber),
    ]);

    const review = await reviewPr(prInfo, diff, files);

    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `${owner.replace("/", "--")}_${repo}_${prNumber}_${timestamp}.md`;
    const outPath = path.join(OUTPUT_DIR, filename);

    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    fs.writeFileSync(outPath, review, "utf-8");
    console.log(`✅ Review saved to: ${outPath}`);
    console.log("\n" + review);
  });

program.parse();
