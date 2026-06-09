#!/usr/bin/env node
/**
 * Peer-review acceptance cases for bounty #2 (issue #2).
 * Codifies manual review checklist so regressions fail CI.
 */
import { execSync } from "node:child_process";
import { readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const repoRoot = join(root, "..", "..");

const claude = readFileSync(join(root, "CLAUDE.md"), "utf8");
const readme = readFileSync(join(root, "README.md"), "utf8");
const validator = readFileSync(join(root, "validate-template.mjs"), "utf8");
const smokeTest = readFileSync(join(__dirname, "smoke-greenfield.sh"), "utf8");
const runCiChecks = readFileSync(join(__dirname, "run-ci-checks.sh"), "utf8");
const workflow = readFileSync(
  join(repoRoot, ".github/workflows/test-nextjs-sqlite-template.yml"),
  "utf8",
);

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
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
];
for (const section of expectedSections) {
  assert(claude.includes(section), `CLAUDE.md includes ${section}`);
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

// Structural validator and greenfield smoke test exist
assert(statSync(join(root, "validate-template.mjs")).isFile(), "validate-template.mjs present");
assert(statSync(join(__dirname, "smoke-greenfield.sh")).isFile(), "smoke-greenfield.sh present");
assert(validator.includes("requiredSections"), "validator enforces required sections");
assert(smokeTest.includes("create-next-app@15"), "smoke test scaffolds Next.js 15 project");
assert(smokeTest.includes('cp "$ROOT/CLAUDE.md"'), "smoke test copies CLAUDE.md into scaffold");
assert(runCiChecks.includes("validate-template.mjs"), "run-ci-checks runs structural validator");
assert(runCiChecks.includes("smoke-greenfield.sh"), "run-ci-checks runs greenfield smoke test");
assert(runCiChecks.includes("peer-review-acceptance.test.mjs"), "run-ci-checks runs peer-review acceptance");
assert(runCiChecks.includes("delivery-verification.test.mjs"), "run-ci-checks runs delivery verification");
assert(
  runCiChecks.includes("delivery verification tests"),
  "run-ci-checks prints delivery verification summary",
);
assert(
  runCiChecks.includes("template_commit_messages="),
  "attribution guard avoids pipefail SIGPIPE from git log | grep",
);
assert(
  runCiChecks.includes("git log -1 --format='%B'"),
  "attribution guard rejects forbidden trailers in HEAD commit message",
);

// Root test entry points delegate to the template CI runner
const makefile = readFileSync(join(repoRoot, "Makefile"), "utf8");
const packageJson = JSON.parse(readFileSync(join(repoRoot, "package.json"), "utf8"));
const gitignore = readFileSync(join(repoRoot, ".gitignore"), "utf8");
assert(statSync(join(repoRoot, "package-lock.json")).isFile(), "package-lock.json locks npm test deps");
assert(gitignore.includes("node_modules/"), ".gitignore excludes node_modules");
assert(gitignore.includes("internal/"), ".gitignore excludes local fleet artifacts");
assert(makefile.includes("run-ci-checks.sh"), "Makefile test target runs unified validation");
assert(makefile.includes("ci-validate:"), "Makefile exposes ci-validate alias for CI runners");
assert(
  packageJson.scripts?.test?.includes("run-ci-checks.sh"),
  "package.json test runs unified validation",
);
assert(
  packageJson.scripts?.["test:ci"]?.includes("run-ci-checks.sh"),
  "package.json test:ci runs unified validation",
);

// CI workflow runs validation and greenfield smoke test
assert(workflow.includes("run-ci-checks.sh"), "CI runs unified validation script");
assert(workflow.includes("pull_request_target"), "CI supports upstream fork PR checks");
assert(workflow.includes("Makefile"), "CI triggers on Makefile changes");
assert(workflow.includes("package.json"), "CI triggers on package.json changes");
assert(workflow.includes("package-lock.json"), "CI triggers on package-lock.json changes");
assert(workflow.includes(".gitignore"), "CI triggers on .gitignore changes");
assert(
  /permissions:\s*\n\s*contents:\s*read/.test(workflow),
  "CI workflow uses read-only contents permission",
);
assert(
  !workflow.includes("github-script") && !workflow.includes("UPSTREAM_STATUS_TOKEN"),
  "CI workflow does not embed privileged github-script tokens",
);

// Runtime CLI checks — validator must pass on the shipped template
const validateOutput = execSync(`node "${join(root, "validate-template.mjs")}"`, {
  encoding: "utf8",
});
assert(
  /Template validation passed with \d+ explicit reasons/.test(validateOutput),
  "validate-template.mjs exits successfully on CLAUDE.md",
);
assert(
  validateOutput.includes("42 explicit reasons") || validateOutput.includes("explicit reasons"),
  "validate-template.mjs reports opinionated reason count",
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
const greenfieldStep4 = greenfieldSection.match(/^4\.\s.+$/m)?.[0] ?? "";
assert(
  /requireOrgMember/.test(greenfieldStep4),
  "Greenfield step 4 mentions requireOrgMember",
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
const createActionExample = claude.match(
  /\/\/ src\/server\/actions\/create-invoice\.ts[\s\S]*?```/,
)?.[0] ?? "";
assert(
  createActionExample.length > 0 && /safeParse/.test(createActionExample),
  "create-invoice action uses safeParse for graceful validation errors",
);

// Peer-review style: Server Actions + Client Components (useActionState form)
assert(
  /useActionState/.test(claude) && /CreateInvoiceForm/.test(claude),
  "Forms section includes useActionState client form example",
);

if (failures.length) {
  console.error(`FAILED peer-review acceptance:\n- ${failures.join("\n- ")}`);
  process.exit(1);
}
