#!/usr/bin/env node
/**
 * Test runner: validates that sample review outputs match the expected format.
 * Also runs end-to-end against 2 real public PRs when GITHUB_TOKEN and ANTHROPIC_API_KEY are set.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const samplesDir = path.join(__dirname, "samples");

const REQUIRED_SECTIONS = [
  "## Summary",
  "## Identified Risks",
  "## Improvement Suggestions",
  "## Confidence Score",
];

let passed = 0;
let failed = 0;

// --- Unit tests: validate sample format ---
const sampleFiles = fs.readdirSync(samplesDir).filter((f) => f.endsWith(".md"));

for (const file of sampleFiles) {
  const content = fs.readFileSync(path.join(samplesDir, file), "utf-8");
  const missing = REQUIRED_SECTIONS.filter((s) => !content.includes(s));
  if (missing.length === 0) {
    console.log(`✅ ${file} — all required sections present`);
    passed++;
  } else {
    console.error(`❌ ${file} — missing sections: ${missing.join(", ")}`);
    failed++;
  }
}

// --- E2E tests: real PRs ---
const { ANTHROPIC_API_KEY, GITHUB_TOKEN } = process.env;

if (ANTHROPIC_API_KEY && GITHUB_TOKEN) {
  console.log("\n🧪 Running E2E tests against real PRs...\n");

  process.env.ANTHROPIC_API_KEY = ANTHROPIC_API_KEY;
  process.env.GITHUB_TOKEN = GITHUB_TOKEN;

  const { parsePrUrl, fetchPrInfo, fetchPrDiff, fetchFiles } = await import(
    "../src/github.js"
  );
  const { reviewPr } = await import("../src/reviewer.js");

  const realPrs = [
    "https://github.com/facebook/react/pull/28542",
    "https://github.com/rust-lang/rust/pull/120000",
  ];

  for (const prUrl of realPrs) {
    try {
      const { owner, repo, prNumber } = parsePrUrl(prUrl);
      console.error(`🔍 E2E: ${owner}/${repo}#${prNumber}`);

      const [prInfo, diff, files] = await Promise.all([
        fetchPrInfo(owner, repo, prNumber),
        fetchPrDiff(owner, repo, prNumber),
        fetchFiles(owner, repo, prNumber),
      ]);

      const review = await reviewPr(prInfo, diff, files);

      const missing = REQUIRED_SECTIONS.filter((s) => !review.includes(s));
      if (missing.length === 0) {
        console.log(
          `✅ E2E ${prUrl} — review valid (${review.length} chars)`
        );
        passed++;

        // Save output
        const ts = new Date().toISOString().replace(/[:.]/g, "-");
        const outFile = path.join(samplesDir, `e2e-${owner}-${repo}-${prNumber}-${ts}.md`);
        fs.writeFileSync(outFile, review, "utf-8");
        console.error(`   Saved to ${outFile}`);
      } else {
        console.error(
          `❌ E2E ${prUrl} — missing: ${missing.join(", ")}`
        );
        failed++;
      }
    } catch (err) {
      console.error(`⚠️  E2E ${prUrl} — skipped: ${err.message}`);
    }
  }
} else {
  console.log("\n💡 Set ANTHROPIC_API_KEY and GITHUB_TOKEN to run E2E tests.");
}

console.log(`\nResults: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
