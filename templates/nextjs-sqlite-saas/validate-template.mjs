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

if (antiPatternRows < 10) {
  console.error(`Expected at least 10 anti-pattern rows, found ${antiPatternRows}.`);
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

console.log(
  `Template validation passed with ${opinionatedCount} explicit reasons and ${smokeTestSteps} smoke-test steps.`,
);
