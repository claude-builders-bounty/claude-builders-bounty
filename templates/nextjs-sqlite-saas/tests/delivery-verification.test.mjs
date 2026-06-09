#!/usr/bin/env node
/**
 * Fleet delivery verification for bounty #2 (issue #2).
 * Guards npm test wiring, CI summary ordering, and peer-review silence on success.
 */
import { readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const repoRoot = join(root, "..", "..");

const tests = [];
function test(name, fn) {
  tests.push({ name, fn });
}

function countAsserts(path) {
  return (readFileSync(path, "utf8").match(/\bassert\(/g) || []).length;
}

test("repo root exposes npm test and test:ci entry points", () => {
  const pkg = JSON.parse(readFileSync(join(repoRoot, "package.json"), "utf8"));
  if (!pkg.scripts?.test?.includes("run-ci-checks.sh")) {
    throw new Error("package.json test script must delegate to run-ci-checks.sh");
  }
  if (!pkg.scripts?.["test:ci"]?.includes("run-ci-checks.sh")) {
    throw new Error("package.json test:ci script must delegate to run-ci-checks.sh");
  }
});

test("ci runner declares delivery and peer-review summary lines", () => {
  const ciScript = readFileSync(join(__dirname, "run-ci-checks.sh"), "utf8");
  if (!ciScript.includes("delivery-verification.test.mjs")) {
    throw new Error("run-ci-checks.sh must run delivery-verification.test.mjs");
  }
  if (!ciScript.includes("delivery verification tests")) {
    throw new Error("run-ci-checks.sh must print delivery verification summary");
  }
  if (!ciScript.includes("peer review acceptance tests passed")) {
    throw new Error("run-ci-checks.sh must print peer review acceptance summary");
  }
  const peerReviewIndex = ciScript.indexOf("peer-review-acceptance.test.mjs");
  const ranTestsIndex = ciScript.indexOf('echo "Ran ${peer_review_tests} tests — OK"');
  if (peerReviewIndex < 0 || ranTestsIndex < 0 || ranTestsIndex <= peerReviewIndex) {
    throw new Error("run-ci-checks.sh must print Ran N tests — OK after peer-review suite");
  }
});

test("peer-review suite is silent on success for CI summary ordering", () => {
  const peerReview = readFileSync(join(__dirname, "peer-review-acceptance.test.mjs"), "utf8");
  if (/console\.log\(['"]OK: peer review acceptance tests passed['"]\)/.test(peerReview)) {
    throw new Error("peer-review-acceptance.test.mjs must not print CI summary (run-ci-checks owns that line)");
  }
  if (/console\.log\([\s\S]*peer-review acceptance checks passed/.test(peerReview)) {
    throw new Error("peer-review-acceptance.test.mjs must stay silent on success");
  }
});

test("template validation and smoke test assets exist", () => {
  for (const rel of ["validate-template.mjs", "CLAUDE.md", "tests/smoke-greenfield.sh"]) {
    if (!statSync(join(root, rel)).isFile()) {
      throw new Error(`missing required template asset: ${rel}`);
    }
  }
});

test("peer-review and delivery suites have minimum coverage", () => {
  const peerReview = countAsserts(join(__dirname, "peer-review-acceptance.test.mjs"));
  const delivery = (readFileSync(join(__dirname, "delivery-verification.test.mjs"), "utf8").match(/^test\(/gm) || [])
    .length;
  if (peerReview < 20) {
    throw new Error(`peer-review-acceptance.test.mjs has ${peerReview} asserts (need >= 20)`);
  }
  if (delivery < 4) {
    throw new Error(`delivery-verification.test.mjs has ${delivery} tests (need >= 4)`);
  }
});

let failed = 0;
for (const { name, fn } of tests) {
  try {
    fn();
  } catch (error) {
    failed += 1;
    console.error(`FAILED ${name}: ${error.message}`);
  }
}

if (failed > 0) {
  process.exit(1);
}
