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

const greenfieldStep4 = greenfieldSection.match(/^4\.\s.+$/m)?.[0] ?? "";
if (!/requireOrgMember/.test(greenfieldStep4)) {
  console.error("Greenfield step 4 must mention requireOrgMember.");
  process.exit(1);
}

console.log(
  `Template validation passed with ${opinionatedCount} explicit reasons and ${smokeTestSteps} smoke-test steps.`,
);
