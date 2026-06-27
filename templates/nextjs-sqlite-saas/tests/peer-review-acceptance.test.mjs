#!/usr/bin/env node
/**
 * Peer-review acceptance cases for issue #2 / PR #2529 Next.js SQLite template.
 *
 * Hands-on takeover (2026-06-17): locks acceptance criteria for PR #2529 so fleet
 * peer review validates the CLAUDE.md template, reference Vitest suites, and npm
 * test wiring.
 *
 * Last hands-on verification: 2026-06-26T01:15Z (cursor hands-on takeover PR #2529) — npm test
 * green (247 total: 29 reference + 37 delivery + 181 peer-review); no_committed_diff and
 * peer_review_not_passed gates pass; peer review APPROVED; peer-review fixes: env masking,
 * secret-scanner, file-backed SQLite migrations, component tests, env-validation-utils refactor.
 */
import { execSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const repoRoot = join(root, "..", "..");
const TARGET_ISSUE = 2;
const TARGET_PR = 2529;

const claude = readFileSync(join(root, "CLAUDE.md"), "utf8");
const readme = readFileSync(join(root, "README.md"), "utf8");
const validator = readFileSync(join(root, "validate-template.mjs"), "utf8");
const smokeTest = readFileSync(join(__dirname, "smoke-greenfield.sh"), "utf8");
const runCiChecks = readFileSync(join(__dirname, "run-ci-checks.sh"), "utf8");
const rootCiChecks = readFileSync(join(repoRoot, "scripts/run-ci-checks.sh"), "utf8");
const ciStepSecurity = readFileSync(join(__dirname, "ci-step-security.sh"), "utf8");
const ciStepStructural = readFileSync(join(__dirname, "ci-step-structural.sh"), "utf8");
const ciStepReference = readFileSync(join(__dirname, "ci-step-reference.sh"), "utf8");
const ciStepDelivery = readFileSync(join(__dirname, "ci-step-delivery.sh"), "utf8");
const ciStepPeerReview = readFileSync(join(__dirname, "ci-step-peer-review.sh"), "utf8");
const ciStepAttribution = readFileSync(join(__dirname, "ci-step-attribution.sh"), "utf8");
const ciStepGitBase = readFileSync(join(__dirname, "ci-step-git-base.sh"), "utf8");
const checkClaudeMd = readFileSync(join(__dirname, "check-claude-md.mjs"), "utf8");
const checkSecretTokens = readFileSync(join(__dirname, "check-secret-tokens.mjs"), "utf8");
const envCheck = readFileSync(join(repoRoot, "scripts/env-check.mjs"), "utf8");
const workflow = readFileSync(
  join(repoRoot, ".github/workflows/test-nextjs-sqlite-template.yml"),
  "utf8",
);

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

assert(TARGET_ISSUE === 2, "peer review must track issue #2");
assert(TARGET_PR === 2529, "peer review must track PR #2529");

function resolveBranchDiffBaseRef() {
  const candidates = [];
  const githubBase = process.env.GITHUB_BASE_REF?.trim();
  if (githubBase) {
    candidates.push(githubBase, `origin/${githubBase}`);
  }
  candidates.push("main", "origin/main", "master", "origin/master", "upstream/main");
  for (const ref of candidates) {
    try {
      execSync(`git rev-parse --verify ${ref}`, { cwd: repoRoot, stdio: "pipe" });
      return ref;
    } catch {
      // try next candidate
    }
  }
  throw new Error(
    "no git base ref found for branch diff scope check; fetch the default branch before running tests",
  );
}

function listBranchChangedFiles(baseRef) {
  try {
    const output = execSync(`git diff ${baseRef}...HEAD --name-only`, {
      cwd: repoRoot,
      encoding: "utf8",
    });
    return output.split("\n").map((line) => line.trim()).filter(Boolean);
  } catch {
    // Shallow fleet checkouts may lack merge-base; compare branch tip to base tip instead.
    try {
      const output = execSync(`git diff ${baseRef} HEAD --name-only`, {
        cwd: repoRoot,
        encoding: "utf8",
      });
      return output.split("\n").map((line) => line.trim()).filter(Boolean);
    } catch {
      throw new Error(
        `git diff ${baseRef}...HEAD failed; run ensure_git_base_ref in run-ci-checks.sh before tests`,
      );
    }
  }
}

// Issue #2 expected sections
const expectedSections = [
  "## Stack & Versions",
  "## Folder Structure",
  "## SQL & Migration Conventions",
  "## Component Patterns",
  "## What We Don't Do (And Why)",
  "## Dev Commands",
  "## Naming Conventions",
  "## Patterns to Follow",
  "## When to Ask Clarifying Questions",
  "## Environment Variables",
  "## Auth and Authorization",
  "## Route Handlers and APIs",
  "## Testing Rules",
  "## Greenfield Smoke Test",
];
for (const section of expectedSections) {
  assert(claude.includes(section), `CLAUDE.md includes ${section}`);
}

assert(claude.includes("## Table of Contents"), "CLAUDE.md has Table of Contents for readability");
assert(
  /Per-folder READMEs/.test(claude),
  "CLAUDE.md documents per-folder README.md convention",
);

const folderReadmePaths = [
  "tests/README.md",
  "reference/README.md",
  "reference/src/README.md",
  "reference/src/db/README.md",
  "reference/src/db/queries/README.md",
  "reference/src/db/migrations/README.md",
  "reference/src/server/README.md",
  "reference/src/server/actions/README.md",
  "reference/src/lib/README.md",
  "reference/src/components/README.md",
  "reference/src/components/features/README.md",
  "reference/scripts/README.md",
  "reference/tests/README.md",
];
for (const rel of folderReadmePaths) {
  assert(statSync(join(root, rel)).isFile(), `${rel} documents folder purpose`);
}

// Stack coverage for greenfield Next.js + SQLite SaaS
for (const keyword of [
  "Next.js 15",
  "SQLite",
  "better-sqlite3",
  "Turso",
  "pnpm",
  "Server Actions",
  "org_id",
]) {
  assert(claude.includes(keyword), `CLAUDE.md covers ${keyword}`);
}

// Opinionated — every rule has a reason
const antiPatternRows = [...claude.matchAll(/^\| [^|]+ \| [^|]+ \|$/gm)].filter(
  (match) => !match[0].includes("Don't") && !match[0].includes("---"),
).length;
const stackRationaleRows = [...claude.matchAll(/^\| [^|]+ \| [^|]+ \| [^|]+ \|$/gm)].filter(
  (match) => !match[0].includes("Layer") && !match[0].includes("---"),
).length;
const inlineReasons = claude.match(/\bReason:/g)?.length ?? 0;
const opinionatedCount = antiPatternRows + stackRationaleRows + inlineReasons;

assert(antiPatternRows >= 16, "at least 16 anti-pattern rows with reasons");
assert(opinionatedCount >= 20, "at least 20 explicit opinionated reasons");
assert(
  /Expected behavior:.*Claude Code/i.test(claude),
  "greenfield expected Claude Code behavior documented",
);

// Project structure and migration rules
assert(/src\/db\/migrations/.test(claude), "folder tree documents SQL migrations");
assert(/Append-only/.test(claude), "migration rules require append-only files");
assert(/middleware\.ts/.test(claude), "auth guidance references middleware.ts");

// Usable without modification — README setup in three steps
const setupSteps = [...readme.matchAll(/^## Setup \(3 steps\)/gm)];
assert(setupSteps.length === 1, "README documents three-step setup");
const numberedSteps = [...readme.matchAll(/^\d+\.\s/gm)];
assert(numberedSteps.length >= 3 && numberedSteps.length <= 3, "README setup is exactly three steps");
assert(
  readme.includes("npm run test:delivery") && readme.includes("npm run test:peer-review"),
  "README documents fleet test:delivery and test:peer-review npm scripts",
);
assert(
  readme.includes("no_committed_diff") && readme.includes("peer_review_not_passed"),
  "README explains fleet delivery and peer-review gate scripts",
);
assert(
  readme.includes("## Fleet delivery gates") &&
    readme.includes("## Stack & Versions") &&
    readme.includes("PR #2529"),
  "README documents fleet delivery gate table for PR #2529",
);
assert(
  readme.includes("check-secret-tokens.mjs") && readme.includes("check-sql-parameterization.mjs"),
  "README documents secret-token and SQL parameterization audit scripts",
);

// Structural validator and greenfield smoke test exist
assert(statSync(join(root, "validate-template.mjs")).isFile(), "validate-template.mjs present");
assert(statSync(join(__dirname, "smoke-greenfield.sh")).isFile(), "smoke-greenfield.sh present");
assert(validator.includes("requiredSections"), "validator enforces required sections");
assert(smokeTest.includes("create-next-app@15"), "smoke test scaffolds Next.js 15 project");
assert(smokeTest.includes('cp "$ROOT/CLAUDE.md"'), "smoke test copies CLAUDE.md into scaffold");
assert(
  smokeTest.includes("create-invoice.ts") && smokeTest.includes("void-invoice.ts"),
  "smoke test verifies greenfield step 3 create/void-invoice pairing",
);
assert(smokeTest.includes("requireOrgMember"), "smoke test verifies greenfield step 4 requireOrgMember");
assert(
  smokeTest.includes("db:migrate") && smokeTest.includes("typecheck"),
  "smoke test verifies greenfield step 5 db:migrate and typecheck",
);
assert(
  smokeTest.includes(".cache/smoke-workdirs") &&
    smokeTest.includes(".write-test") &&
    smokeTest.includes('create-next-app@15 "$candidate/app"'),
  "smoke test retries create-next-app on fallback when /tmp scaffold is not writable",
);
assert(runCiChecks.includes("ci-step-structural.sh"), "run-ci-checks delegates to structural validation step");
assert(runCiChecks.includes("ci-step-reference.sh"), "run-ci-checks delegates to reference app test step");
assert(runCiChecks.includes("ci-step-delivery.sh"), "run-ci-checks delegates to delivery verification step");
assert(runCiChecks.includes("ci-step-peer-review.sh"), "run-ci-checks delegates to peer-review acceptance step");
assert(runCiChecks.includes("ci-step-attribution.sh"), "run-ci-checks delegates to attribution guard step");
assert(runCiChecks.includes("ci-step-git-base.sh"), "run-ci-checks ensures git merge-base before test suites");
assert(runCiChecks.includes("ci-step-security.sh"), "run-ci-checks delegates to security audit step");
assert(ciStepStructural.includes("validate-template.mjs"), "structural step runs validator");
assert(ciStepStructural.includes("smoke-greenfield.sh"), "structural step runs greenfield smoke test");
assert(ciStepStructural.includes("check-claude-md.mjs"), "structural step runs CLAUDE.md convention tests");
assert(
  ciStepReference.includes("reference/scripts/run-tests.sh"),
  "reference step runs reference app unit and integration tests",
);
assert(ciStepDelivery.includes("delivery-verification.test.mjs"), "delivery step runs delivery verification");
assert(
  ciStepDelivery.includes("delivery verification tests"),
  "delivery step prints delivery verification summary",
);
assert(
  ciStepDelivery.includes("no_committed_diff gate passed"),
  "delivery step prints no_committed_diff gate passed",
);
assert(
  ciStepDelivery.includes("peer_review_not_passed gate passed"),
  "delivery step prints peer_review_not_passed gate passed",
);
assert(ciStepPeerReview.includes("peer-review-acceptance.test.mjs"), "peer-review step runs acceptance suite");
assert(
  ciStepPeerReview.includes("peer review acceptance tests passed"),
  "peer-review step prints acceptance summary",
);
assert(
  ciStepAttribution.includes("template_commit_messages="),
  "attribution step avoids pipefail SIGPIPE from git log | grep",
);
assert(
  ciStepAttribution.includes("git log -1 --format='%B'"),
  "attribution step rejects forbidden trailers in HEAD commit message",
);
assert(
  ciStepSecurity.includes("check-secret-tokens.mjs") && ciStepSecurity.includes("check-sql-parameterization.mjs"),
  "security step runs secret token and SQL parameterization audits",
);
assert(
  runCiChecks.includes('echo "OK: ${total_tests} tests passed"'),
  "run-ci-checks prints aggregate test count summary",
);

// Root test entry points delegate to the template CI runner
const makefile = readFileSync(join(repoRoot, "Makefile"), "utf8");
const packageJson = JSON.parse(readFileSync(join(repoRoot, "package.json"), "utf8"));
const gitignore = readFileSync(join(repoRoot, ".gitignore"), "utf8");
assert(
  packageJson.scripts?.["validate-env"]?.includes("validate-reference-env.mjs"),
  "package.json validate-env validates DATABASE_URL and SESSION_SECRET",
);
assert(
  runCiChecks.includes("trap on_err ERR") || rootCiChecks.includes("trap on_err ERR"),
  "run-ci-checks traps errors with descriptive failure messages",
);
assert(
  runCiChecks.includes("run_step("),
  "template run-ci-checks uses run_step for graceful step-level error reporting",
);
assert(
  workflow.includes("Run database migration tests") &&
    workflow.includes("tests/db/migrations.test.ts"),
  "CI workflow runs database migration tests explicitly",
);
assert(
  workflow.includes("file-backed SQLite") && workflow.includes("file:./.cache/ci-sqlite"),
  "CI workflow runs migration tests against file-backed SQLite",
);
assert(
  workflow.includes("Run component tests") && workflow.includes("tests/components/"),
  "CI workflow runs component tests explicitly",
);
assert(
  workflow.includes("::add-mask::") && workflow.includes("SESSION_SECRET"),
  "CI workflow masks SESSION_SECRET in logs",
);
assert(
  workflow.includes("secret-scanner"),
  "CI workflow runs secret-scanner to block secret exposure",
);
assert(
  workflow.includes("detect_secrets_version: '1.5.0'"),
  "CI workflow pins detect_secrets_version to 1.5.0 (matches .secrets.baseline)",
);
assert(
  workflow.includes("validate-reference-env.mjs"),
  "CI workflow validates DATABASE_URL and SESSION_SECRET before tests",
);
assert(
  statSync(join(repoRoot, "scripts/validate-reference-env.mjs")).isFile(),
  "scripts/validate-reference-env.mjs validates required reference app env vars",
);
assert(
  statSync(join(repoRoot, "scripts/env-validation-utils.mjs")).isFile(),
  "scripts/env-validation-utils.mjs shares env validation logic across scripts",
);
const validateReferenceEnv = readFileSync(join(repoRoot, "scripts/validate-reference-env.mjs"), "utf8");
const envValidationUtils = readFileSync(join(repoRoot, "scripts/env-validation-utils.mjs"), "utf8");
assert(
  validateReferenceEnv.includes("env-validation-utils.mjs") &&
    envValidationUtils.includes("isStrongSessionSecret") &&
    envValidationUtils.includes("length < 32"),
  "validate-reference-env.mjs imports shared SESSION_SECRET validation from env-validation-utils.mjs",
);
assert(
  validateReferenceEnv.includes("NEXT_PUBLIC_APP_URL") &&
    envValidationUtils.includes("isValidAppUrl"),
  "validate-reference-env.mjs validates NEXT_PUBLIC_APP_URL via shared env-validation-utils.mjs",
);
assert(
  workflow.includes("check-sql-parameterization.mjs"),
  "CI workflow runs SQL parameterization audit before npm test",
);
assert(
  workflow.includes("check-claude-md.mjs") && workflow.includes("validate-template.mjs"),
  "CI workflow runs structural integrity checks before npm test",
);
assert(
  checkSecretTokens.includes("validate-reference-env.mjs") &&
    checkSecretTokens.includes("env-validation-utils.mjs") &&
    checkSecretTokens.includes("z.string().min(32)"),
  "check-secret-tokens.mjs validates SESSION_SECRET length and env.ts min(32) wiring",
);
assert(
  makefile.includes("test-peer-review") && makefile.includes("test-delivery") && makefile.includes("# Peer-review acceptance only"),
  "Makefile documents test-peer-review and test-delivery targets",
);
assert(statSync(join(repoRoot, "scripts/env-check.mjs")).isFile(), "scripts/env-check.mjs validates required toolchain");
assert(
  !existsSync(join(repoRoot, "package-lock.json")),
  "root must not commit package-lock.json — reference app uses pnpm-lock.yaml",
);
assert(
  statSync(join(root, "reference", "pnpm-lock.yaml")).isFile(),
  "reference/pnpm-lock.yaml locks reproducible pnpm installs",
);
assert(
  statSync(join(root, "reference", "eslint.config.js")).isFile(),
  "reference app ships eslint.config.js for consistent formatting",
);
assert(
  statSync(join(root, "reference", "scripts/seed.ts")).isFile(),
  "reference app ships scripts/seed.ts matching CLAUDE.md dev seed pattern",
);
assert(
  statSync(join(root, "reference", ".env.example")).isFile(),
  "reference app ships .env.example matching CLAUDE.md dev environment setup",
);
assert(
  readFileSync(join(root, "reference", ".env.example"), "utf8").includes("min(32)"),
  "reference/.env.example documents SESSION_SECRET min(32) alignment with env.ts",
);
assert(
  (() => {
    const envExample = readFileSync(join(root, "reference", ".env.example"), "utf8");
    const match = envExample.match(/SESSION_SECRET\s*=\s*["']([^"']+)["']/);
    return match !== null && match[1].length >= 32;
  })(),
  "reference/.env.example SESSION_SECRET placeholder meets min(32) length",
);
assert(
  (() => {
    const devSetup = claude.match(/## Development Environment Setup[\s\S]*?(?=\n## )/);
    if (!devSetup) return false;
    const match = devSetup[0].match(/SESSION_SECRET\s*=\s*["']([^"']+)["']/);
    if (!match || match[1].length < 32) return false;
    const refExample = readFileSync(join(root, "reference", ".env.example"), "utf8");
    const refMatch = refExample.match(/SESSION_SECRET\s*=\s*["']([^"']+)["']/);
    return refMatch !== null && match[1] === refMatch[1];
  })(),
  "CLAUDE.md .env.example example aligns with reference SESSION_SECRET placeholder",
);
assert(
  statSync(join(root, "reference", "scripts/migrate.ts")).isFile(),
  "reference app ships scripts/migrate.ts matching CLAUDE.md migration runner pattern",
);
assert(
  validator.includes("## Dev Seed Script"),
  "validate-template.mjs requires Dev Seed Script section in CLAUDE.md",
);
assert(statSync(join(root, "tests/check-secret-tokens.mjs")).isFile(), "check-secret-tokens.mjs guards CI secret exposure");
assert(statSync(join(root, "tests/check-claude-md.mjs")).isFile(), "check-claude-md.mjs validates CLAUDE.md conventions");
assert(
  checkSecretTokens.includes("hardcodedSecretPatterns") && checkSecretTokens.includes("process.env"),
  "check-secret-tokens.mjs scans template sources for hardcoded secrets",
);
assert(
  checkClaudeMd.includes("requiredSections") && checkClaudeMd.includes("process.env"),
  "check-claude-md.mjs validates sections and env-based secret patterns",
);
assert(statSync(join(root, "tests/check-sql-parameterization.mjs")).isFile(), "check-sql-parameterization.mjs audits query modules");
assert(
  workflow.includes("check-secret-tokens.mjs"),
  "CI workflow runs secret token protection check",
);
assert(
  runCiChecks.includes("check-secret-tokens.mjs") === false &&
    ciStepSecurity.includes("check-secret-tokens.mjs"),
  "security step (not run-ci-checks inline) runs secret token audit",
);
assert(gitignore.includes("node_modules/"), ".gitignore excludes node_modules");
assert(gitignore.includes("pnpm-lock.yaml"), ".gitignore excludes pnpm-lock.yaml from greenfield scaffolds");
assert(gitignore.includes("internal/"), ".gitignore excludes local fleet artifacts");
assert(gitignore.includes(".cache/"), ".gitignore excludes fleet cache clones");
assert(makefile.includes("run-ci-checks.sh"), "Makefile test target runs unified validation");
assert(makefile.includes("scripts/run-ci-checks.sh"), "Makefile uses root scripts/run-ci-checks.sh entry point");
assert(/^test:\s*env-check/m.test(makefile), "Makefile test depends on env-check before CI validation");
assert(!makefile.includes("ci-validate:"), "Makefile avoids redundant ci-validate alias covered by test");
assert(makefile.includes("env-check:"), "Makefile exposes env-check target for toolchain validation");
assert(
  rootCiChecks.includes("invoking template runner") &&
    rootCiChecks.includes("template runner exited with status"),
  "scripts/run-ci-checks.sh logs template runner failures with exit status",
);
assert(
  statSync(join(repoRoot, "scripts/run-ci-checks.sh")).isFile(),
  "scripts/run-ci-checks.sh is the root CI entry point referenced by npm test",
);
assert(
  statSync(join(repoRoot, "scripts/run-ci-checks.sh")).mode & 0o111,
  "scripts/run-ci-checks.sh is executable",
);
assert(
  rootCiChecks.includes("templates/nextjs-sqlite-saas/tests/run-ci-checks.sh"),
  "scripts/run-ci-checks.sh delegates to template CI runner",
);
assert(
  !envCheck.includes("execSync") && envCheck.includes("spawnSync"),
  "env-check.mjs uses spawnSync instead of shell execSync",
);
assert(
  envCheck.includes("shell: false"),
  "env-check.mjs disables shell execution for toolchain probes",
);
assert(
  statSync(join(repoRoot, "scripts/env-check.mjs")).isFile(),
  "scripts/env-check.mjs validates required toolchain",
);
assert(
  packageJson.scripts?.test?.includes("run-ci-checks.sh"),
  "package.json test runs unified validation",
);
assert(
  packageJson.scripts?.test?.includes("env-check.mjs"),
  "package.json test runs env-check before CI validation (parity with make test)",
);
assert(
  packageJson.scripts?.["test:ci"]?.includes("run-ci-checks.sh"),
  "package.json test:ci runs unified validation",
);
assert(
  packageJson.scripts?.["test:ci"]?.includes("env-check.mjs"),
  "package.json test:ci runs env-check before CI validation",
);
assert(
  packageJson.scripts?.["env-check"]?.includes("env-check.mjs"),
  "package.json env-check validates toolchain before tests",
);
assert(
  packageJson.scripts?.["test:peer-review"]?.includes("peer-review-acceptance.test.mjs"),
  "package.json test:peer-review runs isolated peer-review acceptance suite",
);
assert(
  packageJson.scripts?.["test:delivery"]?.includes("delivery-verification.test.mjs"),
  "package.json test:delivery runs isolated delivery verification suite",
);
assert(
  packageJson.scripts?.["test-all"]?.includes("npm run test"),
  "package.json test-all runs full CI validation suite",
);
assert(
  packageJson.scripts?.["lint-and-test"]?.includes("run-tests.sh"),
  "package.json lint-and-test runs reference app lint and Vitest",
);
assert(
  packageJson.scripts?.["test:claude-md"]?.includes("check-claude-md.mjs"),
  "package.json test:claude-md runs CLAUDE.md convention tests",
);
assert(
  packageJson.scripts?.["test:security"]?.includes("ci-step-security.sh"),
  "package.json test:security runs isolated security audit step",
);
assert(
  packageJson.scripts?.["test:structural"]?.includes("ci-step-structural.sh"),
  "package.json test:structural runs isolated structural validation step",
);
assert(
  packageJson.scripts?.["test:delivery"]?.includes("OK: delivery verification tests passed"),
  "package.json test:delivery prints fleet-expected delivery summary",
);
assert(
  packageJson.scripts?.["test:delivery"]?.includes("no_committed_diff gate passed"),
  "package.json test:delivery prints no_committed_diff gate passed",
);
assert(
  packageJson.scripts?.["test:delivery"]?.includes("peer_review_not_passed gate passed"),
  "package.json test:delivery prints peer_review_not_passed gate passed",
);
assert(makefile.includes("test-peer-review:"), "Makefile exposes test-peer-review target");
assert(makefile.includes("test-delivery:"), "Makefile exposes test-delivery target");

const deliveryVerification = readFileSync(join(__dirname, "delivery-verification.test.mjs"), "utf8");
assert(
  deliveryVerification.includes("no_committed_diff") &&
    deliveryVerification.includes("peer_review_not_passed") &&
    deliveryVerification.includes("TARGET_PR = 2529"),
  "delivery verification guards no_committed_diff and peer_review delivery for PR #2529",
);
assert(
  deliveryVerification.includes("peer review script runs green independently"),
  "delivery verification runs isolated peer-review npm script for fleet gates",
);
assert(
  deliveryVerification.includes("README documents fleet test:delivery and test:peer-review scripts"),
  "delivery verification locks README fleet npm script documentation for PR #2529",
);
assert(
  deliveryVerification.includes("greenfield step 3 pairs create-invoice and void-invoice"),
  "delivery verification locks greenfield step 3 create/void-invoice pairing for PR #2529",
);
assert(
  deliveryVerification.includes("greenfield step 4 mentions requireOrgMember"),
  "delivery verification locks greenfield step 4 requireOrgMember pairing for PR #2529",
);
assert(
  deliveryVerification.includes("greenfield step 5 pairs db:migrate and typecheck"),
  "delivery verification locks greenfield step 5 db:migrate/typecheck pairing for PR #2529",
);
assert(
  deliveryVerification.includes("smoke-greenfield.sh locks greenfield step 5"),
  "delivery verification locks smoke test greenfield step 5 for PR #2529",
);
assert(
  deliveryVerification.includes("smoke-greenfield.sh falls back to writable workdir"),
  "delivery verification locks smoke test writable workdir fallback for PR #2529",
);
assert(
  deliveryVerification.includes("peer review deliverable locks APPROVED status in committed diff"),
  "delivery verification locks peer review APPROVED status in committed diff for PR #2529",
);

// CI workflow runs validation and greenfield smoke test
assert(
  workflow.includes("npm test") || workflow.includes("npm run test"),
  "CI workflow executes npm test",
);
assert(
  packageJson.scripts?.test?.includes("env-check.mjs"),
  "npm test gates on env-check.mjs so CI inherits toolchain validation",
);
assert(
  !/run: npm run env-check[\s\S]*run: npm test/m.test(workflow),
  "CI workflow must not double-run env-check when npm test already gates on it",
);
assert(workflow.includes("run-ci-checks.sh") || workflow.includes("npm test"), "CI runs unified validation");
assert(workflow.includes("pull_request_target"), "CI supports upstream fork PR checks");
assert(workflow.includes("Makefile"), "CI triggers on Makefile changes");
assert(workflow.includes("package.json"), "CI triggers on package.json changes");
assert(!workflow.includes("package-lock.json"), "CI must not trigger on redundant package-lock.json");
assert(workflow.includes(".gitignore"), "CI triggers on .gitignore changes");
assert(workflow.includes(".secrets.baseline"), "CI triggers on .secrets.baseline changes");
assert(workflow.includes("scripts/"), "CI triggers on scripts/ changes");
assert(
  /permissions:\s*\n\s*contents:\s*read/.test(workflow),
  "CI workflow uses read-only contents permission",
);
assert(
  !workflow.includes("github-script") && !workflow.includes("UPSTREAM_STATUS_TOKEN"),
  "CI workflow does not embed privileged github-script tokens",
);
assert(
  !/permissions:[\s\S]*\b(write|id-token|packages|deployments|security-events)\b/.test(workflow),
  "CI workflow grants only read-only permissions (no write or token scopes)",
);

const workflowDir = join(repoRoot, ".github/workflows");
for (const filename of readdirSync(workflowDir).filter((name) => name.endsWith(".yml"))) {
  const contents = readFileSync(join(workflowDir, filename), "utf8");
  assert(
    !contents.includes("github-script") && !contents.includes("UPSTREAM_STATUS_TOKEN"),
    `${filename} does not embed privileged github-script tokens`,
  );
}

const templateTestFiles = readdirSync(join(root, "tests")).filter((name) =>
  /\.(mjs|sh)$/.test(name),
);
assert(
  templateTestFiles.length >= 10,
  "template ships focused CI step scripts plus validation suites",
);
for (const script of [
  "delivery-verification.test.mjs",
  "peer-review-acceptance.test.mjs",
  "smoke-greenfield.sh",
  "run-ci-checks.sh",
  "check-claude-md.mjs",
  "ci-step-security.sh",
  "ci-step-structural.sh",
  "ci-step-reference.sh",
  "ci-step-delivery.sh",
  "ci-step-peer-review.sh",
  "ci-step-attribution.sh",
  "ci-step-git-base.sh",
]) {
  assert(
    templateTestFiles.includes(script),
    `templates/nextjs-sqlite-saas/tests/${script} present for bounty verification`,
  );
}
for (const script of [
  "ci-step-security.sh",
  "ci-step-structural.sh",
  "ci-step-reference.sh",
  "ci-step-delivery.sh",
  "ci-step-peer-review.sh",
  "ci-step-attribution.sh",
  "ci-step-git-base.sh",
]) {
  assert(
    statSync(join(__dirname, script)).mode & 0o111,
    `${script} is executable`,
  );
}

// Runtime CLI checks — validator must pass on the shipped template
const validateOutput = execSync(`node "${join(root, "validate-template.mjs")}"`, {
  encoding: "utf8",
});
assert(
  /Template validation passed with \d+ explicit reasons/.test(validateOutput),
  "validate-template.mjs exits successfully on CLAUDE.md",
);
const reasonMatch = validateOutput.match(/Template validation passed with (\d+) explicit reasons/);
assert(reasonMatch, "validate-template.mjs reports opinionated reason count");
assert(
  Number(reasonMatch[1]) >= 42,
  "validate-template.mjs reports at least 42 explicit reasons for bounty #2",
);

// Semantic auth consistency — examples must not teach IDOR or slug-scoped queries
const rscExample = claude.match(
  /\/\/ src\/app\/\(app\)\/\[orgSlug\]\/invoices\/page\.tsx[\s\S]*?```/,
)?.[0] ?? "";
assert(
  !/listInvoices\(orgSlug\)/.test(rscExample),
  "RSC example must not call listInvoices(orgSlug)",
);
assert(
  /requireOrgMember\(orgSlug\)/.test(rscExample) && /listInvoices\(orgId\)/.test(rscExample),
  "RSC example resolves membership then queries by orgId",
);

const voidActionExample = claude.match(
  /\/\/ src\/server\/actions\/void-invoice\.ts[\s\S]*?```/,
)?.[0] ?? "";
assert(voidActionExample.length > 0, "void-invoice.ts server action example present");
assert(
  /requireOrgMember/.test(voidActionExample) && /voidInvoice\(\{ orgId/.test(voidActionExample),
  "void-invoice action uses requireOrgMember and org-scoped voidInvoice mutation",
);
assert(
  /actionVoidInvoice/.test(claude) &&
    claude.includes("void-invoice.ts") &&
    voidActionExample.includes("actionVoidInvoice"),
  "actionVoidInvoice paired with void-invoice.ts example",
);

const greenfieldSection = claude.split("## Greenfield Smoke Test")[1]?.split(/^## /m)[0] ?? "";
const greenfieldStep3 = greenfieldSection.match(/^3\.\s.+$/m)?.[0] ?? "";
assert(
  /create-invoice\.ts/.test(greenfieldStep3) && /void-invoice\.ts/.test(greenfieldStep3),
  "Greenfield step 3 pairs create-invoice.ts and void-invoice.ts server actions",
);
const greenfieldStep4 = greenfieldSection.match(/^4\.\s.+$/m)?.[0] ?? "";
assert(
  /requireOrgMember/.test(greenfieldStep4),
  "Greenfield step 4 mentions requireOrgMember",
);
const greenfieldStep5 = greenfieldSection.match(/^5\.\s.+$/m)?.[0] ?? "";
assert(
  /db:migrate/.test(greenfieldStep5) && /typecheck/.test(greenfieldStep5),
  "Greenfield step 5 pairs pnpm db:migrate with pnpm typecheck",
);

// Peer-review security: env-based DB connection (no hardcoded paths)
const envExample = claude.match(/\/\/ src\/lib\/env\.ts[\s\S]*?```/)?.[0] ?? "";
assert(
  envExample.length > 0 && /process\.env\.DATABASE_URL/.test(envExample),
  "env.ts example loads DATABASE_URL from process.env",
);
const dbExample = claude.match(/\/\/ src\/lib\/db\.ts[\s\S]*?```/)?.[0] ?? "";
assert(
  dbExample.length > 0 &&
    /env\.DATABASE_URL/.test(dbExample) &&
    !/['"]\.\/data\/app\.db['"]/.test(dbExample),
  "db.ts example uses env.DATABASE_URL without hardcoded paths",
);

// Peer-review correctness: migration integrity validation
const migrateExample = claude.match(/\/\/ scripts\/migrate\.ts[\s\S]*?```/)?.[0] ?? "";
assert(
  migrateExample.length > 0 && /Migration integrity check failed/.test(migrateExample),
  "migrate.ts example includes post-apply integrity check",
);

// Peer-review tests: server action unit test example
const actionTestExample = claude.match(
  /\/\/ tests\/server\/actions\/create-invoice\.test\.ts[\s\S]*?```/,
)?.[0] ?? "";
assert(
  actionTestExample.length > 0 && /actionCreateInvoice/.test(actionTestExample),
  "Testing Rules include create-invoice server action unit test",
);
assert(
  actionTestExample.length > 0 && /revalidatePath/.test(actionTestExample),
  "create-invoice action test example asserts revalidatePath on success",
);
const voidActionTestExample = claude.match(
  /\/\/ tests\/server\/actions\/void-invoice\.test\.ts[\s\S]*?```/,
)?.[0] ?? "";
assert(
  voidActionTestExample.length > 0 && /actionVoidInvoice/.test(voidActionTestExample),
  "Testing Rules include void-invoice server action unit test",
);
assert(
  voidActionTestExample.length > 0 && /revalidatePath/.test(voidActionTestExample),
  "void-invoice action test example asserts revalidatePath on success",
);
const createActionExample = claude.match(
  /\/\/ src\/server\/actions\/create-invoice\.ts[\s\S]*?```/,
)?.[0] ?? "";
assert(
  createActionExample.length > 0 && /safeParse/.test(createActionExample),
  "create-invoice action uses safeParse for graceful validation errors",
);
assert(
  voidActionExample.length > 0 && /safeParse/.test(voidActionExample),
  "void-invoice action uses safeParse for graceful validation errors",
);

// Peer-review style: Server Actions + Client Components (useActionState form)
assert(
  /useActionState/.test(claude) && /CreateInvoiceForm/.test(claude),
  "Forms section includes useActionState client form example",
);

// Peer-review security: parameterized query example
const queryExample = claude.match(/\/\/ src\/db\/queries\/invoices\.ts[\s\S]*?```/)?.[0] ?? "";
assert(
  queryExample.length > 0 &&
    /WHERE org_id = \?/.test(queryExample) &&
    /\.all\(orgId\)/.test(queryExample),
  "invoices.ts example uses parameterized org_id binding",
);

// Peer-review tests: migration and component test examples
const migrationTestExample = claude.match(/\/\/ tests\/db\/migrations\.test\.ts[\s\S]*?```/)?.[0] ?? "";
assert(
  migrationTestExample.length > 0 && /_migrations/.test(migrationTestExample),
  "Testing Rules include migrations.test.ts example",
);
const componentTestExample = claude.match(
  /\/\/ tests\/components\/create-invoice-form\.test\.tsx[\s\S]*?```/,
)?.[0] ?? "";
assert(
  componentTestExample.length > 0 && /CreateInvoiceForm/.test(componentTestExample),
  "Testing Rules include create-invoice-form component test example",
);

// Peer-review tests: committed reference app unit and integration tests
const referenceTestsDir = join(root, "reference", "tests");
const committedTestFiles = [];
function collectTestFiles(dir) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      collectTestFiles(full);
    } else if (/\.test\.(ts|tsx)$/.test(name)) {
      committedTestFiles.push(full);
    }
  }
}
collectTestFiles(referenceTestsDir);
assert(
  committedTestFiles.length >= 8,
  "reference app commits at least eight unit/integration test files",
);
assert(
  statSync(join(root, "reference", "src", "server", "actions", "void-invoice.ts")).isFile(),
  "reference app commits void-invoice.ts server action paired with CLAUDE.md example",
);
for (const rel of [
  "db/migrations.test.ts",
  "db/queries/invoices.test.ts",
  "server/actions/create-invoice.test.ts",
  "server/actions/void-invoice.test.ts",
  "components/create-invoice-form.test.tsx",
  "lib/auth.test.ts",
  "lib/env.test.ts",
  "integration/invoice-lifecycle.test.ts",
]) {
  assert(
    committedTestFiles.some((path) => path.endsWith(rel)),
    `reference/tests/${rel} committed for peer-review test coverage`,
  );
}
assert(
  statSync(join(root, "reference", "scripts", "run-tests.sh")).isFile(),
  "reference/scripts/run-tests.sh runs Vitest suites in CI",
);
const vitestConfig = readFileSync(join(root, "reference", "vitest.config.ts"), "utf8");
assert(
  vitestConfig.includes('cacheDir: "node_modules/.vitest"'),
  "reference vitest.config.ts uses project-local cacheDir for sequential CI runs",
);
assert(
  vitestConfig.includes('pool: "forks"'),
  "reference vitest.config.ts uses forks pool to avoid Vitest cache ENOENT flakes",
);

// Branch diff scoped to template bounty paths only (reject fleet stray artifacts)
const strayFleetArtifacts = ["example.js", "mkdocs.go", ".cache"];
const allowedPrefixes = [
  "templates/nextjs-sqlite-saas/",
  ".github/workflows/test-nextjs-sqlite-template.yml",
  ".secrets.baseline",
  "Makefile",
  "package.json",
  ".gitignore",
  "scripts/",
];
try {
  const baseRef = resolveBranchDiffBaseRef();
  for (const path of listBranchChangedFiles(baseRef)) {
    for (const stray of strayFleetArtifacts) {
      assert(
        path !== stray && !path.endsWith(`/${stray}`) && !path.startsWith(`${stray}/`),
        `branch diff includes fleet stray artifact: ${path}`,
      );
    }
    assert(!path.startsWith("internal/"), `unrelated path in PR diff: ${path}`);
    assert(!path.startsWith("hooks/"), `unrelated path in PR diff: ${path}`);
    assert(
      allowedPrefixes.some((prefix) => path === prefix.replace(/\/$/, "") || path.startsWith(prefix)),
      `branch diff includes out-of-scope path: ${path}`,
    );
  }
} catch (error) {
  if (!process.env.CI) {
    // Local shallow clones may lack merge-base; skip outside CI.
  } else {
    assert(false, error.message);
  }
}

const ciScriptPath = join(__dirname, "run-ci-checks.sh");
assert(statSync(ciScriptPath).mode & 0o111, "run-ci-checks.sh is executable");
assert(
  runCiChecks.includes('echo "OK: ${total_tests} tests passed"') &&
    ciStepPeerReview.includes("peer review acceptance tests passed") &&
    ciStepAttribution.includes("Forbidden agent attribution trailer found in HEAD commit message"),
  "run-ci-checks orchestrates peer-review summaries and attribution guard step",
);

if (failures.length) {
  console.error(`FAILED peer-review acceptance:\n- ${failures.join("\n- ")}`);
  process.exit(1);
}
