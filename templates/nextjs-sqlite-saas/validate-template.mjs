import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const claudePath = process.argv[2]
  ? resolve(process.argv[2])
  : new URL("./CLAUDE.md", import.meta.url);

const text = readFileSync(claudePath, "utf8");

const requiredSections = [
  "## Stack & Versions",
  "## Dev Commands",
  "## Folder Structure",
  "## Naming Conventions",
  "## SQL & Migration Conventions",
  "## Component Patterns",
  "## Patterns to Follow",
  "## What We Don't Do (And Why)",
  "## When to Ask Clarifying Questions",
  "## Environment Variables",
  "## Auth and Authorization",
  "## Route Handlers and APIs",
  "## Dev Seed Script",
  "## Testing Rules",
  "## Greenfield Smoke Test",
];

const requiredKeywords = [
  "Next.js 15",
  "SQLite",
  "better-sqlite3",
  "Turso",
  "pnpm",
  "Server Actions",
  "org_id",
];

const missingSections = requiredSections.filter((section) => !text.includes(section));
if (missingSections.length > 0) {
  console.error(
    `Missing required sections:\n${missingSections.map((item) => `- ${item}`).join("\n")}`,
  );
  process.exit(1);
}

const missingKeywords = requiredKeywords.filter((keyword) => !text.includes(keyword));
if (missingKeywords.length > 0) {
  console.error(
    `Missing required stack coverage:\n${missingKeywords.map((item) => `- ${item}`).join("\n")}`,
  );
  process.exit(1);
}

const antiPatternRows = [...text.matchAll(/^\| [^|]+ \| [^|]+ \|$/gm)].filter(
  (match) => !match[0].includes("Don't") && !match[0].includes("---"),
).length;

if (antiPatternRows < 16) {
  console.error(`Expected at least 16 anti-pattern rows, found ${antiPatternRows}.`);
  process.exit(1);
}

const stackRationaleRows = [...text.matchAll(/^\| [^|]+ \| [^|]+ \| [^|]+ \|$/gm)].filter(
  (match) => !match[0].includes("Layer") && !match[0].includes("---"),
).length;

const inlineReasons = text.match(/\bReason:/g)?.length ?? 0;

const greenfieldSection = text.split("## Greenfield Smoke Test")[1]?.split(/^## /m)[0] ?? "";
const smokeTestSteps = greenfieldSection.match(/^\d+\.\s+/gm)?.length ?? 0;
const opinionatedCount = antiPatternRows + stackRationaleRows + inlineReasons;

if (opinionatedCount < 20) {
  console.error(`Expected at least 20 opinionated reasons, found ${opinionatedCount}.`);
  process.exit(1);
}

if (smokeTestSteps < 4) {
  console.error(`Expected at least 4 greenfield smoke-test steps, found ${smokeTestSteps}.`);
  process.exit(1);
}

if (!/Expected behavior:.*Claude Code/i.test(text)) {
  console.error("Missing explicit expected Claude Code greenfield behavior.");
  process.exit(1);
}

if (!/middleware\.ts/.test(text)) {
  console.error("Missing middleware.ts in folder structure or auth guidance.");
  process.exit(1);
}

const rscExample = text.match(
  /\/\/ src\/app\/\(app\)\/\[orgSlug\]\/invoices\/page\.tsx[\s\S]*?```/,
)?.[0] ?? "";
if (/listInvoices\(orgSlug\)/.test(rscExample)) {
  console.error("RSC example must not call listInvoices(orgSlug); use orgId after requireOrgMember.");
  process.exit(1);
}
if (!/requireOrgMember\(orgSlug\)/.test(rscExample) || !/listInvoices\(orgId\)/.test(rscExample)) {
  console.error("RSC example must call requireOrgMember(orgSlug) then listInvoices(orgId).");
  process.exit(1);
}

const voidActionExample = text.match(
  /\/\/ src\/server\/actions\/void-invoice\.ts[\s\S]*?```/,
)?.[0] ?? "";
if (!voidActionExample) {
  console.error("Missing void-invoice.ts server action example.");
  process.exit(1);
}
if (!/requireOrgMember/.test(voidActionExample) || !/voidInvoice\(\{ orgId/.test(voidActionExample)) {
  console.error("void-invoice action must use requireOrgMember and org-scoped voidInvoice mutation.");
  process.exit(1);
}
if (!/actionVoidInvoice/.test(text) || !text.includes("void-invoice.ts")) {
  console.error("actionVoidInvoice must be paired with void-invoice.ts example.");
  process.exit(1);
}

const greenfieldStep3 = greenfieldSection.match(/^3\.\s.+$/m)?.[0] ?? "";
if (!/create-invoice\.ts/.test(greenfieldStep3) || !/void-invoice\.ts/.test(greenfieldStep3)) {
  console.error("Greenfield step 3 must pair create-invoice.ts and void-invoice.ts server actions.");
  process.exit(1);
}

const greenfieldStep4 = greenfieldSection.match(/^4\.\s.+$/m)?.[0] ?? "";
if (!/requireOrgMember/.test(greenfieldStep4)) {
  console.error("Greenfield step 4 must mention requireOrgMember.");
  process.exit(1);
}

const greenfieldStep5 = greenfieldSection.match(/^5\.\s.+$/m)?.[0] ?? "";
if (!/db:migrate/.test(greenfieldStep5) || !/typecheck/.test(greenfieldStep5)) {
  console.error("Greenfield step 5 must pair pnpm db:migrate with pnpm typecheck.");
  process.exit(1);
}

const envExample = text.match(/\/\/ src\/lib\/env\.ts[\s\S]*?```/)?.[0] ?? "";
if (!envExample || !/process\.env\.DATABASE_URL/.test(envExample)) {
  console.error("env.ts example must load DATABASE_URL from process.env.");
  process.exit(1);
}

const dbExample = text.match(/\/\/ src\/lib\/db\.ts[\s\S]*?```/)?.[0] ?? "";
if (!dbExample || !/env\.DATABASE_URL/.test(dbExample) || /['"]\.\/data\/app\.db['"]/.test(dbExample)) {
  console.error("db.ts example must use env.DATABASE_URL without hardcoded paths.");
  process.exit(1);
}

const migrateExample = text.match(/\/\/ scripts\/migrate\.ts[\s\S]*?```/)?.[0] ?? "";
if (!migrateExample || !/Migration integrity check failed/.test(migrateExample)) {
  console.error("migrate.ts example must include post-apply integrity check.");
  process.exit(1);
}

const seedExample = text.match(/\/\/ scripts\/seed\.ts[\s\S]*?```/)?.[0] ?? "";
if (!seedExample || !/NODE_ENV.*production/.test(seedExample)) {
  console.error("seed.ts example must block production with NODE_ENV guard.");
  process.exit(1);
}
if (!/ON CONFLICT\(id\) DO NOTHING/.test(seedExample)) {
  console.error("seed.ts example must use idempotent upsert.");
  process.exit(1);
}

const actionTestExample = text.match(
  /\/\/ tests\/server\/actions\/create-invoice\.test\.ts[\s\S]*?```/,
)?.[0] ?? "";
if (!actionTestExample || !/actionCreateInvoice/.test(actionTestExample)) {
  console.error("Testing Rules must include create-invoice server action unit test example.");
  process.exit(1);
}
if (!/revalidatePath/.test(actionTestExample)) {
  console.error("create-invoice test example must assert revalidatePath on success.");
  process.exit(1);
}

const voidActionTestExample = text.match(
  /\/\/ tests\/server\/actions\/void-invoice\.test\.ts[\s\S]*?```/,
)?.[0] ?? "";
if (!voidActionTestExample || !/actionVoidInvoice/.test(voidActionTestExample)) {
  console.error("Testing Rules must include void-invoice server action unit test example.");
  process.exit(1);
}
if (!/revalidatePath/.test(voidActionTestExample)) {
  console.error("void-invoice test example must assert revalidatePath on success.");
  process.exit(1);
}

const createActionExample = text.match(
  /\/\/ src\/server\/actions\/create-invoice\.ts[\s\S]*?```/,
)?.[0] ?? "";
if (!createActionExample || !/safeParse/.test(createActionExample)) {
  console.error("create-invoice action must use safeParse for graceful validation errors.");
  process.exit(1);
}

if (!/useActionState/.test(text) || !/CreateInvoiceForm/.test(text)) {
  console.error("Forms section must include useActionState client form example.");
  process.exit(1);
}

const queryExample = text.match(/\/\/ src\/db\/queries\/invoices\.ts[\s\S]*?```/)?.[0] ?? "";
if (!queryExample || !/WHERE org_id = \?/.test(queryExample) || !/\.all\(orgId\)/.test(queryExample)) {
  console.error("invoices.ts example must use parameterized org_id binding.");
  process.exit(1);
}

const migrationTestExample = text.match(/\/\/ tests\/db\/migrations\.test\.ts[\s\S]*?```/)?.[0] ?? "";
if (!migrationTestExample || !/_migrations/.test(migrationTestExample)) {
  console.error("Testing Rules must include migrations.test.ts example.");
  process.exit(1);
}

const componentTestExample = text.match(
  /\/\/ tests\/components\/create-invoice-form\.test\.tsx[\s\S]*?```/,
)?.[0] ?? "";
if (!componentTestExample || !/CreateInvoiceForm/.test(componentTestExample)) {
  console.error("Testing Rules must include create-invoice-form component test example.");
  process.exit(1);
}

console.log(
  `Template validation passed with ${opinionatedCount} explicit reasons and ${smokeTestSteps} smoke-test steps.`,
);
