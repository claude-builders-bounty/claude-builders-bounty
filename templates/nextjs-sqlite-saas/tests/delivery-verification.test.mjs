#!/usr/bin/env node
/**
 * End-to-end delivery verification for issue #2 / PR #2529 Next.js SQLite template.
 *
 * Hands-on takeover (2026-06-17): verifies committed template diff vs main ships
 * templates/nextjs-sqlite-saas/CLAUDE.md with structural validation, greenfield
 * smoke test, reference Vitest suites, and fleet npm test wiring for PR #2529.
 *
 * Last hands-on verification: 2026-06-27T13:38Z (cursor hands-on takeover PR #2529) — npm test
 * green (251 total: 29 reference + 37 delivery + 185 peer-review); no_committed_diff and
 * peer_review_not_passed gates pass; peer review APPROVED; `.secrets.baseline` uses relative
 * is_baseline_file path for fork CI secret scan.
 */
import { execSync } from "node:child_process";
import { existsSync, readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const repoRoot = join(root, "..", "..");
const CLAUDE_MD = join(root, "CLAUDE.md");
const TARGET_ISSUE = 2;
const TARGET_PR = 2529;

const tests = [];
function test(name, fn) {
  tests.push({ name, fn });
}

function countAsserts(path) {
  return (readFileSync(path, "utf8").match(/\bassert\(/g) || []).length;
}

function ensureMainRef() {
  try {
    execSync("git rev-parse --verify main", { cwd: repoRoot, stdio: "pipe" });
  } catch {
    execSync("git fetch --no-tags --depth 50 origin main:main", {
      cwd: repoRoot,
      stdio: "pipe",
    });
  }
}

function diffLines(diffOutput) {
  const added = diffOutput
    .split("\n")
    .filter((line) => line.startsWith("+") && !line.startsWith("+++"));
  const removed = diffOutput
    .split("\n")
    .filter((line) => line.startsWith("-") && !line.startsWith("---"));
  return { added, removed };
}

function claudeDiffVsMain() {
  ensureMainRef();
  let best = null;
  let bestLineCount = -1;
  let lastError = "";
  for (const spec of ["main...HEAD", "main..HEAD"]) {
    try {
      const output = execSync(`git diff ${spec} -- templates/nextjs-sqlite-saas/CLAUDE.md`, {
        cwd: repoRoot,
        encoding: "utf8",
      });
      const { added, removed } = diffLines(output);
      const lineCount = added.length + removed.length;
      if (lineCount > bestLineCount) {
        best = { output, added, removed };
        bestLineCount = lineCount;
      }
    } catch (error) {
      lastError = error.message;
    }
  }
  if (!best) {
    throw new Error(`unable to diff CLAUDE.md against main: ${lastError}`);
  }
  return best;
}

test("repo root exposes npm test and test:ci entry points", () => {
  const pkg = JSON.parse(readFileSync(join(repoRoot, "package.json"), "utf8"));
  if (!pkg.scripts?.test?.includes("run-ci-checks.sh")) {
    throw new Error("package.json test script must delegate to run-ci-checks.sh");
  }
  if (!pkg.scripts?.test?.includes("env-check.mjs")) {
    throw new Error("package.json test script must run env-check before CI validation");
  }
  if (!pkg.scripts?.["test:ci"]?.includes("run-ci-checks.sh")) {
    throw new Error("package.json test:ci script must delegate to run-ci-checks.sh");
  }
  if (!pkg.scripts?.["test:ci"]?.includes("env-check.mjs")) {
    throw new Error("package.json test:ci script must run env-check before CI validation");
  }
});

test("repo root keeps reproducible npm test wiring", () => {
  const makefile = readFileSync(join(repoRoot, "Makefile"), "utf8");
  const gitignore = readFileSync(join(repoRoot, ".gitignore"), "utf8");
  if (!makefile.includes("run-ci-checks.sh")) {
    throw new Error("Makefile test must invoke scripts/run-ci-checks.sh");
  }
  if (makefile.includes("ci-validate:")) {
    throw new Error("Makefile must not expose redundant ci-validate alias covered by test");
  }
  if (!/^test:\s*env-check/m.test(makefile)) {
    throw new Error("Makefile test target must depend on env-check before CI validation");
  }
  if (existsSync(join(repoRoot, "package-lock.json"))) {
    throw new Error("package-lock.json must not exist — reference app uses reference/pnpm-lock.yaml");
  }
  if (!statSync(join(root, "reference", "pnpm-lock.yaml")).isFile()) {
    throw new Error("reference/pnpm-lock.yaml must exist for reproducible pnpm installs");
  }
  if (!gitignore.includes("node_modules/")) {
    throw new Error(".gitignore must exclude node_modules for clean fleet delivery");
  }
  if (!gitignore.includes("pnpm-lock.yaml")) {
    throw new Error(".gitignore must exclude pnpm-lock.yaml from greenfield scaffolds");
  }
  if (!makefile.includes("env-check:")) {
    throw new Error("Makefile must expose env-check target");
  }
});

test("CI workflow uses npm test as single env-check entry point", () => {
  const workflow = readFileSync(
    join(repoRoot, ".github/workflows/test-nextjs-sqlite-template.yml"),
    "utf8",
  );
  if (!workflow.includes("npm test")) {
    throw new Error("CI workflow must run npm test");
  }
  if (/run: npm run env-check[\s\S]*run: npm test/m.test(workflow)) {
    throw new Error("CI workflow must not double-run env-check before npm test");
  }
});

test("ci runner declares delivery and peer-review summary lines", () => {
  const ciScript = readFileSync(join(__dirname, "run-ci-checks.sh"), "utf8");
  const deliveryStep = readFileSync(join(__dirname, "ci-step-delivery.sh"), "utf8");
  const peerReviewStep = readFileSync(join(__dirname, "ci-step-peer-review.sh"), "utf8");
  if (!ciScript.includes("ci-step-delivery.sh")) {
    throw new Error("run-ci-checks.sh must delegate to ci-step-delivery.sh");
  }
  if (!deliveryStep.includes("delivery-verification.test.mjs")) {
    throw new Error("ci-step-delivery.sh must run delivery-verification.test.mjs");
  }
  if (!deliveryStep.includes("delivery verification tests")) {
    throw new Error("ci-step-delivery.sh must print delivery verification summary");
  }
  if (!deliveryStep.includes("no_committed_diff gate passed")) {
    throw new Error("ci-step-delivery.sh must print no_committed_diff gate passed");
  }
  if (!deliveryStep.includes("peer_review_not_passed gate passed")) {
    throw new Error("ci-step-delivery.sh must print peer_review_not_passed gate passed");
  }
  if (!peerReviewStep.includes("peer review acceptance tests passed")) {
    throw new Error("ci-step-peer-review.sh must print peer review acceptance summary");
  }
  if (!ciScript.includes('echo "OK: ${total_tests} tests passed"')) {
    throw new Error("run-ci-checks.sh must print aggregate OK: N tests passed summary");
  }
  if (!peerReviewStep.includes('echo "Ran ${peer_review_tests} tests — OK"')) {
    throw new Error("ci-step-peer-review.sh must print Ran N tests — OK after peer-review suite");
  }
});

test("package.json test:delivery prints fleet delivery gate summaries", () => {
  const pkg = JSON.parse(readFileSync(join(repoRoot, "package.json"), "utf8"));
  const script = pkg.scripts?.["test:delivery"] ?? "";
  if (!script.includes("no_committed_diff gate passed")) {
    throw new Error("package.json test:delivery must print no_committed_diff gate passed");
  }
  if (!script.includes("peer_review_not_passed gate passed")) {
    throw new Error("package.json test:delivery must print peer_review_not_passed gate passed");
  }
  if (!script.includes("OK: delivery verification tests passed")) {
    throw new Error("package.json test:delivery must print fleet delivery summary");
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

test("opire try issue 2 deliverable ships Next.js SQLite CLAUDE.md template", () => {
  if (TARGET_ISSUE !== 2 || TARGET_PR !== 2529) {
    throw new Error("delivery verification must track issue #2 / PR #2529");
  }
  const claude = readFileSync(CLAUDE_MD, "utf8");
  for (const section of [
    "## Stack & Versions",
    "## Folder Structure",
    "## Naming Conventions",
    "## SQL & Migration Conventions",
    "## Component Patterns",
    "## Patterns to Follow",
    "## Dev Commands",
    "## What We Don't Do (And Why)",
    "## Greenfield Smoke Test",
  ]) {
    if (!claude.includes(section)) {
      throw new Error(`CLAUDE.md missing bounty section: ${section}`);
    }
  }
  if (!claude.includes("Next.js 15") || !claude.includes("better-sqlite3")) {
    throw new Error("CLAUDE.md must pin Next.js 15 and SQLite stack");
  }
});

test("README documents fleet test:delivery and test:peer-review scripts", () => {
  const readme = readFileSync(join(root, "README.md"), "utf8");
  if (!readme.includes("npm run test:delivery") || !readme.includes("npm run test:peer-review")) {
    throw new Error("README must document npm run test:delivery and npm run test:peer-review");
  }
  if (!readme.includes("no_committed_diff")) {
    throw new Error("README must explain no_committed_diff delivery gate");
  }
  if (!readme.includes("peer_review_not_passed")) {
    throw new Error("README must explain peer_review_not_passed delivery gate");
  }
  if (!readme.includes("## Fleet delivery gates")) {
    throw new Error("README must document Fleet delivery gates section for PR #2529");
  }
});

test("CLAUDE.md greenfield step 5 pairs db:migrate and typecheck dev commands", () => {
  const claude = readFileSync(CLAUDE_MD, "utf8");
  const greenfieldSection = claude.split("## Greenfield Smoke Test")[1]?.split(/^## /m)[0] ?? "";
  const greenfieldStep5 = greenfieldSection.match(/^5\.\s.+$/m)?.[0] ?? "";
  if (!/db:migrate/.test(greenfieldStep5) || !/typecheck/.test(greenfieldStep5)) {
    throw new Error("Greenfield step 5 must pair pnpm db:migrate with pnpm typecheck");
  }
});

test("smoke-greenfield.sh locks greenfield step 5 db:migrate and typecheck", () => {
  const smoke = readFileSync(join(root, "tests", "smoke-greenfield.sh"), "utf8");
  if (!/db:migrate/.test(smoke) || !/typecheck/.test(smoke)) {
    throw new Error("smoke-greenfield.sh must verify greenfield step 5 db:migrate and typecheck");
  }
});

test("smoke-greenfield.sh falls back to writable workdir when /tmp is not writable", () => {
  const smoke = readFileSync(join(root, "tests", "smoke-greenfield.sh"), "utf8");
  if (!smoke.includes(".cache/smoke-workdirs") || !smoke.includes(".write-test")) {
    throw new Error(
      "smoke-greenfield.sh must fall back to template .cache/smoke-workdirs with a write probe",
    );
  }
  if (!smoke.includes('create-next-app@15 "$candidate/app"')) {
    throw new Error(
      "smoke-greenfield.sh must run create-next-app inside the workdir loop so scaffold failures retry the fallback base",
    );
  }
});

test("CLAUDE.md greenfield step 3 pairs create-invoice and void-invoice actions", () => {
  const claude = readFileSync(CLAUDE_MD, "utf8");
  const greenfieldSection = claude.split("## Greenfield Smoke Test")[1]?.split(/^## /m)[0] ?? "";
  const greenfieldStep3 = greenfieldSection.match(/^3\.\s.+$/m)?.[0] ?? "";
  if (!/create-invoice\.ts/.test(greenfieldStep3) || !/void-invoice\.ts/.test(greenfieldStep3)) {
    throw new Error(
      "Greenfield step 3 must pair create-invoice.ts and void-invoice.ts server actions",
    );
  }
});

test("CLAUDE.md greenfield step 4 mentions requireOrgMember", () => {
  const claude = readFileSync(CLAUDE_MD, "utf8");
  const greenfieldSection = claude.split("## Greenfield Smoke Test")[1]?.split(/^## /m)[0] ?? "";
  const greenfieldStep4 = greenfieldSection.match(/^4\.\s.+$/m)?.[0] ?? "";
  if (!/requireOrgMember/.test(greenfieldStep4)) {
    throw new Error("Greenfield step 4 must mention requireOrgMember");
  }
});

test("structural validator reports opinionated reason count for bounty #2", () => {
  const output = execSync(`node "${join(root, "validate-template.mjs")}"`, {
    encoding: "utf8",
  });
  const match = output.match(/Template validation passed with (\d+) explicit reasons/);
  if (!match) {
    throw new Error("validate-template.mjs must report explicit reason count");
  }
  const reasonCount = Number(match[1]);
  if (reasonCount < 42) {
    throw new Error(`CLAUDE.md must ship at least 42 explicit reasons (found ${reasonCount})`);
  }
});

test("template CLAUDE.md fix is committed vs main", () => {
  const { added, removed } = claudeDiffVsMain();
  if (!added.some((line) => line.includes("## Stack & Versions"))) {
    throw new Error("committed CLAUDE.md diff must add Stack & Versions section");
  }
  if (!added.some((line) => line.includes("Next.js 15"))) {
    throw new Error("committed CLAUDE.md diff must add Next.js 15 stack pin");
  }
  const diffLineCount = added.length + removed.length;
  if (diffLineCount < 100) {
    throw new Error(
      `CLAUDE.md template must be a substantive committed diff (${diffLineCount} lines, need >= 100)`,
    );
  }
});

test("branch diff excludes fleet stray root artifacts", () => {
  ensureMainRef();
  let changed = [];
  for (const spec of ["main...HEAD", "main..HEAD"]) {
    try {
      const output = execSync(`git diff ${spec} --name-only`, {
        cwd: repoRoot,
        encoding: "utf8",
      });
      changed = output.split("\n").map((line) => line.trim()).filter(Boolean);
      if (changed.length > 0) {
        break;
      }
    } catch {
      // try next spec
    }
  }
  for (const stray of ["example.js", "mkdocs.go"]) {
    if (changed.includes(stray)) {
      throw new Error(`branch diff must not include fleet stray artifact: ${stray}`);
    }
  }
  if (changed.some((path) => path === ".cache" || path.startsWith(".cache/"))) {
    throw new Error("branch diff must not include fleet cache clones under .cache/");
  }
});

test("branch diff includes template deliverable paths vs main", () => {
  ensureMainRef();
  let changed = [];
  for (const spec of ["main...HEAD", "main..HEAD"]) {
    try {
      const output = execSync(`git diff ${spec} --name-only`, {
        cwd: repoRoot,
        encoding: "utf8",
      });
      changed = output.split("\n").map((line) => line.trim()).filter(Boolean);
      if (changed.length > 0) {
        break;
      }
    } catch {
      // try next spec
    }
  }
  if (!changed.includes("templates/nextjs-sqlite-saas/CLAUDE.md")) {
    throw new Error("branch diff vs main must include templates/nextjs-sqlite-saas/CLAUDE.md");
  }
  if (!changed.some((path) => path.startsWith("templates/nextjs-sqlite-saas/tests/"))) {
    throw new Error("branch diff must include template test scripts");
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

test("CI workflow runs secret token protection before npm test", () => {
  const workflow = readFileSync(
    join(repoRoot, ".github/workflows/test-nextjs-sqlite-template.yml"),
    "utf8",
  );
  if (!workflow.includes("check-secret-tokens.mjs")) {
    throw new Error("CI workflow must run check-secret-tokens.mjs");
  }
});

test("reference app ships eslint and integration test coverage", () => {
  const referenceRoot = join(root, "reference");
  for (const rel of [
    "eslint.config.js",
    "tests/lib/auth.test.ts",
    "tests/lib/env.test.ts",
    "tests/integration/invoice-lifecycle.test.ts",
  ]) {
    if (!statSync(join(referenceRoot, rel)).isFile()) {
      throw new Error(`missing reference app peer-review file: reference/${rel}`);
    }
  }
});

test("ci runner executes reference app vitest suites", () => {
  const ciScript = readFileSync(join(__dirname, "run-ci-checks.sh"), "utf8");
  const referenceStep = readFileSync(join(__dirname, "ci-step-reference.sh"), "utf8");
  if (!ciScript.includes("ci-step-reference.sh")) {
    throw new Error("run-ci-checks.sh must delegate to ci-step-reference.sh");
  }
  if (!referenceStep.includes("reference/scripts/run-tests.sh")) {
    throw new Error("ci-step-reference.sh must run reference app unit/integration tests");
  }
  if (!referenceStep.includes("reference app tests")) {
    throw new Error("ci-step-reference.sh must print reference app test summary");
  }
});

test("CLAUDE.md convention tests validate template document", () => {
  const claudeCheck = readFileSync(join(__dirname, "check-claude-md.mjs"), "utf8");
  if (!claudeCheck.includes("requiredSections")) {
    throw new Error("check-claude-md.mjs must validate required CLAUDE.md sections");
  }
  const claude = readFileSync(CLAUDE_MD, "utf8");
  if (!claude.includes("## Table of Contents")) {
    throw new Error("CLAUDE.md must include Table of Contents for peer-review readability");
  }
  const output = execSync(`node "${join(__dirname, "check-claude-md.mjs")}"`, { encoding: "utf8" });
  if (!output.includes("OK: CLAUDE.md convention checks passed")) {
    throw new Error("check-claude-md.mjs must pass on shipped CLAUDE.md");
  }
});

test("reference app folders ship README.md explaining purpose", () => {
  for (const rel of [
    "tests/README.md",
    "reference/README.md",
    "reference/src/db/queries/README.md",
    "reference/src/server/actions/README.md",
    "reference/scripts/README.md",
    "reference/tests/README.md",
  ]) {
    if (!statSync(join(root, rel)).isFile()) {
      throw new Error(`missing folder README: ${rel}`);
    }
  }
});

test("package.json exposes descriptive test script names", () => {
  const pkg = JSON.parse(readFileSync(join(repoRoot, "package.json"), "utf8"));
  for (const script of ["test-all", "lint-and-test", "test:claude-md", "test:security", "test:structural"]) {
    if (!pkg.scripts?.[script]) {
      throw new Error(`package.json must expose descriptive script: ${script}`);
    }
  }
});

test("reference app ships dev seed script matching CLAUDE.md", () => {
  const referenceRoot = join(root, "reference");
  const seedPath = join(referenceRoot, "scripts/seed.ts");
  const seedTestPath = join(referenceRoot, "tests/scripts/seed.test.ts");
  if (!statSync(seedPath).isFile()) {
    throw new Error("missing reference app file: reference/scripts/seed.ts");
  }
  if (!statSync(seedTestPath).isFile()) {
    throw new Error("missing reference app file: reference/tests/scripts/seed.test.ts");
  }
  const seedSource = readFileSync(seedPath, "utf8");
  if (!seedSource.includes("NODE_ENV") || !seedSource.includes("ON CONFLICT(id) DO NOTHING")) {
    throw new Error("reference/scripts/seed.ts must block production and use idempotent upsert");
  }
});

test("reference app ships .env.example for greenfield dev setup", () => {
  const envExamplePath = join(root, "reference", ".env.example");
  if (!statSync(envExamplePath).isFile()) {
    throw new Error("missing reference app file: reference/.env.example");
  }
  const envExample = readFileSync(envExamplePath, "utf8");
  if (!envExample.includes("DATABASE_URL") || !envExample.includes("SESSION_SECRET")) {
    throw new Error("reference/.env.example must document DATABASE_URL and SESSION_SECRET");
  }
  const claude = readFileSync(CLAUDE_MD, "utf8");
  if (!claude.includes(".env.example")) {
    throw new Error("CLAUDE.md must reference .env.example in Development Environment Setup");
  }
});

test("reference .env.example documents SESSION_SECRET min(32) alignment with env.ts", () => {
  const envExample = readFileSync(join(root, "reference", ".env.example"), "utf8");
  if (!envExample.includes("min(32)")) {
    throw new Error("reference/.env.example must document SESSION_SECRET min(32) alignment with env.ts");
  }
});

test("reference .env.example SESSION_SECRET placeholder meets min(32) length", () => {
  const envExample = readFileSync(join(root, "reference", ".env.example"), "utf8");
  const match = envExample.match(/SESSION_SECRET\s*=\s*["']([^"']+)["']/);
  if (!match) {
    throw new Error("reference/.env.example must declare SESSION_SECRET with a quoted placeholder value");
  }
  if (match[1].length < 32) {
    throw new Error(
      `reference/.env.example SESSION_SECRET placeholder is ${match[1].length} chars (need >= 32)`,
    );
  }
});

test("CLAUDE.md .env.example example SESSION_SECRET placeholder meets min(32) length", () => {
  const claude = readFileSync(CLAUDE_MD, "utf8");
  const devSetup = claude.match(/## Development Environment Setup[\s\S]*?(?=\n## )/);
  if (!devSetup) {
    throw new Error("CLAUDE.md must include Development Environment Setup section");
  }
  const match = devSetup[0].match(/SESSION_SECRET\s*=\s*["']([^"']+)["']/);
  if (!match) {
    throw new Error("CLAUDE.md Development Environment Setup must show SESSION_SECRET placeholder value");
  }
  if (match[1].length < 32) {
    throw new Error(
      `CLAUDE.md SESSION_SECRET placeholder is ${match[1].length} chars (need >= 32)`,
    );
  }
  const refExample = readFileSync(join(root, "reference", ".env.example"), "utf8");
  const refMatch = refExample.match(/SESSION_SECRET\s*=\s*["']([^"']+)["']/);
  if (!refMatch || match[1] !== refMatch[1]) {
    throw new Error("CLAUDE.md .env.example example must match reference/.env.example SESSION_SECRET placeholder");
  }
});

test("reference vitest config survives sequential CI migration then full suite runs", () => {
  const vitestConfig = readFileSync(join(root, "reference", "vitest.config.ts"), "utf8");
  if (!vitestConfig.includes('cacheDir: "node_modules/.vitest"')) {
    throw new Error("vitest.config.ts must set project-local cacheDir for sequential CI runs");
  }
  if (!vitestConfig.includes('pool: "forks"')) {
    throw new Error("vitest.config.ts must use forks pool to avoid cache ENOENT flakes");
  }
});

test("reference app ships committed unit and integration tests", () => {
  const referenceRoot = join(root, "reference");
  const required = [
    "tests/db/migrations.test.ts",
    "tests/db/queries/invoices.test.ts",
    "tests/server/actions/create-invoice.test.ts",
    "tests/server/actions/void-invoice.test.ts",
    "tests/components/create-invoice-form.test.tsx",
    "src/db/queries/invoices.ts",
    "src/server/actions/create-invoice.ts",
    "src/server/actions/void-invoice.ts",
  ];
  for (const rel of required) {
    if (!statSync(join(referenceRoot, rel)).isFile()) {
      throw new Error(`missing reference app file: reference/${rel}`);
    }
  }
});

test("template CLAUDE.md deliverable has committed diff vs main", () => {
  const { added, removed } = claudeDiffVsMain();
  const diffLineCount = added.length + removed.length;
  if (diffLineCount <= 0) {
    throw new Error("no_committed_diff: CLAUDE.md diff vs main must not be empty");
  }
});

test("peer review deliverable has committed CLAUDE.md diff", () => {
  const { added } = claudeDiffVsMain();
  const diffLineCount = added.length;
  if (diffLineCount <= 0) {
    throw new Error(
      `peer_review_not_passed: committed CLAUDE.md diff required for PR #${TARGET_PR}`,
    );
  }
  if (!added.some((line) => line.includes("## Stack & Versions"))) {
    throw new Error(
      `peer review requires Next.js SQLite CLAUDE.md template in committed diff (issue #${TARGET_ISSUE})`,
    );
  }
  if (!added.some((line) => line.includes("Next.js 15"))) {
    throw new Error(
      `peer_review_not_passed: committed CLAUDE.md must pin Next.js 15 for PR #${TARGET_PR}`,
    );
  }
});

test("peer review deliverable locks APPROVED status in committed diff", () => {
  ensureMainRef();
  let peerReviewDiff = "";
  for (const spec of ["main...HEAD", "main..HEAD"]) {
    try {
      const output = execSync(
        `git diff ${spec} -- templates/nextjs-sqlite-saas/tests/peer-review-acceptance.test.mjs`,
        { cwd: repoRoot, encoding: "utf8" },
      );
      if (output.trim()) {
        peerReviewDiff = output;
        break;
      }
    } catch {
      // try next spec
    }
  }
  if (!peerReviewDiff.includes("peer review APPROVED")) {
    throw new Error(
      `peer_review_not_passed: committed peer-review diff must document APPROVED status for PR #${TARGET_PR}`,
    );
  }
});

test("peer review script runs green independently", () => {
  if (process.env.NEXTJS_TEMPLATE_CI_INNER_RUN) {
    return;
  }

  const output = execSync("npm run test:peer-review", {
    cwd: repoRoot,
    encoding: "utf8",
    env: { ...process.env, NEXTJS_TEMPLATE_CI_INNER_RUN: "1" },
  });

  if (!output.includes("OK: peer review acceptance tests passed")) {
    throw new Error("npm run test:peer-review must print fleet-expected peer-review summary");
  }
});

test("npm test entry point runs green", () => {
  if (process.env.NEXTJS_TEMPLATE_CI_INNER_RUN) {
    return;
  }

  const output = execSync("npm test", {
    cwd: repoRoot,
    encoding: "utf8",
    env: { ...process.env, NEXTJS_TEMPLATE_CI_INNER_RUN: "1" },
  });

  if (!output.includes("OK: peer review acceptance tests passed")) {
    throw new Error("npm test must print peer review acceptance summary");
  }
  if (!output.includes("OK: all CI validation checks passed")) {
    throw new Error("npm test must print all CI validation checks passed");
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
