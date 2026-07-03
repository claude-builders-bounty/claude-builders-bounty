#!/usr/bin/env node
/**
 * CLAUDE.md convention tests — validates the template document adheres to
 * bounty #2 guidelines (sections, stack pins, env-based secrets, code examples).
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const claude = readFileSync(join(root, "CLAUDE.md"), "utf8");

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

const requiredSections = [
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
  "## Dev Seed Script",
];

for (const section of requiredSections) {
  assert(claude.includes(section), `CLAUDE.md includes ${section}`);
}

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

const envExample = claude.match(/\/\/ src\/lib\/env\.ts[\s\S]*?```/)?.[0] ?? "";
assert(
  envExample.length > 0 && /process\.env\.DATABASE_URL/.test(envExample),
  "env.ts example loads DATABASE_URL from process.env",
);
assert(
  envExample.length > 0 && /process\.env\.SESSION_SECRET/.test(envExample),
  "env.ts example loads SESSION_SECRET from process.env",
);

const dbExample = claude.match(/\/\/ src\/lib\/db\.ts[\s\S]*?```/)?.[0] ?? "";
assert(
  dbExample.length > 0 &&
    /env\.DATABASE_URL/.test(dbExample) &&
    !/['"]\.\/data\/app\.db['"]/.test(dbExample),
  "db.ts example uses env.DATABASE_URL without hardcoded paths",
);

const seedExample = claude.match(/\/\/ scripts\/seed\.ts[\s\S]*?```/)?.[0] ?? "";
assert(
  seedExample.length > 0 && /NODE_ENV/.test(seedExample) && /ON CONFLICT/.test(seedExample),
  "seed.ts example blocks production and uses idempotent upsert",
);

const antiPatternRows = [...claude.matchAll(/^\| [^|]+ \| [^|]+ \|$/gm)].filter(
  (match) => !match[0].includes("Don't") && !match[0].includes("---"),
).length;
assert(antiPatternRows >= 16, "at least 16 anti-pattern rows with reasons");

const greenfieldSection = claude.split("## Greenfield Smoke Test")[1]?.split(/^## /m)[0] ?? "";
assert(
  /create-invoice\.ts/.test(greenfieldSection) && /void-invoice\.ts/.test(greenfieldSection),
  "Greenfield section pairs create-invoice and void-invoice actions",
);
assert(/requireOrgMember/.test(greenfieldSection), "Greenfield section mentions requireOrgMember");
assert(
  /db:migrate/.test(greenfieldSection) && /typecheck/.test(greenfieldSection),
  "Greenfield section pairs db:migrate and typecheck",
);

if (failures.length) {
  console.error(`FAILED CLAUDE.md convention checks:\n- ${failures.join("\n- ")}`);
  process.exit(1);
}

console.log(`OK: CLAUDE.md convention checks passed (${requiredSections.length} sections)`);
