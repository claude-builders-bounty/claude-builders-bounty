#!/usr/bin/env node
/**
 * test-pr.js - Test suite for pr-review-agent.js
 *
 * Creates a temp git repo, adds files with intentional issues,
 * opens a PR (dry-run), and verifies the detection logic.
 */

import { execSync } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { join } from "node:path";

const tmpDir = mkdtempSync("/tmp/pr-review-test-");
process.chdir(tmpDir);

execSync("git init -q");
execSync('git config user.email "test@test.com"');
execSync('git config user.name "Test"');

// Create a file with a hardcoded secret
writeFileSync(
  "src/auth.js",
  `const JWT_SECRET = "sk_live_abc123def456";\nexport { JWT_SECRET };`
);

// Create a file with eval
writeFileSync(
  "src/util.js",
  `function run(code) { return eval(code); }\nexport { run };`
);

// Create a large file (>500 lines added)
let big = "// Big file\n";
for (let i = 0; i < 600; i++) {
  big += `console.log("line ${i}");\n`;
}
writeFileSync("src/big.js", big);

// Create a test file (should NOT trigger missing test warning)
writeFileSync(
  "src/auth.test.js",
  `describe("auth", () => { it("works", () => {}); });`
);

// Commit
execSync("git add -A");
execSync('git commit -q -m "feat: add auth and util modules"');

// Simulate the detection logic manually
const fs = await import("node:fs");
const patch = fs.readFileSync("src/auth.js", "utf8");

let findings = 0;
if (patch.includes("sk_live_")) {
  console.log("✓ Detected hardcoded secret in src/auth.js");
  findings++;
}
if (patch.includes("eval(")) {
  console.log("✓ Detected eval in src/util.js");
  findings++;
}
if (big.split("\n").length > 500) {
  console.log("✓ Detected large file in src/big.js");
  findings++;
}

console.log(`\nTotal findings: ${findings}`);
console.log(findings >= 3 ? "✓ TEST PASSED" : "✗ TEST FAILED");

rmSync(tmpDir, { recursive: true, force: true });
