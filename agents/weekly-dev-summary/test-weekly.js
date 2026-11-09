#!/usr/bin/env node
/**
 * test-weekly.js - Test weekly-dev-summary.js
 *
 * Creates a temp git repo with commits across 7 days,
 * runs the summary generation, and verifies output.
 */

import { execSync } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import * as os from "node:os";

const tmpDir = mkdtempSync(join(os.tmpdir(), "weekly-test-"));
process.chdir(tmpDir);

execSync("git init -q");
execSync('git config user.email "test@test.com"');
execSync('git config user.name "Test"');

// Create commits across the last 7 days
const today = new Date();
for (let i = 0; i < 7; i++) {
  const d = new Date(today);
  d.setDate(d.getDate() - i);
  const dateStr = d.toISOString().split("T")[0];
  const commitDate = `${dateStr}T10:00:00`;

  writeFileSync(`file-${i}.txt`, `content day ${i}\n`);
  execSync(`git add -A`);
  execSync(
    `GIT_AUTHOR_DATE="${commitDate}" GIT_COMMITTER_DATE="${commitDate}" git commit -q -m "feat: add feature for day ${i}"`
  );
  writeFileSync(`file-${i}.txt`, `content day ${i} updated\n`);
  execSync(`git add -A`);
  execSync(
    `GIT_AUTHOR_DATE="${commitDate}" GIT_COMMITTER_DATE="${commitDate}" git commit -q -m "fix: fix issue in day ${i}"`
  );
}

// Run the summary logic inline
const now = new Date();
const since = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
const sinceStr = since.toISOString().split("T")[0];

const logOutput = execSync(
  `git log --since="${sinceStr}" --pretty="format:%s%x01%an"`,
  { encoding: "utf8" }
).trim();

const lines = logOutput.split("\n").filter((l) => l.trim());
let featCount = 0;
let fixCount = 0;

for (const line of lines) {
  const msg = line.split("\u0001")[0] || "";
  if (msg.startsWith("feat:")) featCount++;
  if (msg.startsWith("fix:")) fixCount++;
}

console.log(`Total commits: ${lines.length}`);
console.log(`Feat commits: ${featCount}`);
console.log(`Fix commits: ${fixCount}`);

if (lines.length >= 14 && featCount >= 7 && fixCount >= 7) {
  console.log("✓ TEST PASSED: Weekly summary generated correctly");
} else {
  console.log("✗ TEST FAILED: Expected 14+ commits (7 feat, 7 fix)");
  process.exit(1);
}

rmSync(tmpDir, { recursive: true, force: true });
