#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const templatePath = join(here, "CLAUDE.md");
const text = readFileSync(templatePath, "utf8");

const checks = [
  ["stack section", /^## Stack And Versions$/m],
  ["dev commands section", /^## Dev Commands$/m],
  ["folder structure section", /^## Folder Structure$/m],
  ["naming conventions section", /^## Naming Conventions$/m],
  ["sqlite and migrations section", /^## SQLite And Migration Rules$/m],
  ["component patterns section", /^## Component Patterns$/m],
  ["anti-patterns section", /^## What We Do Not Do And Why$/m],
  ["Claude operating instructions", /^## Claude Operating Instructions$/m],
  ["Next.js 15", /Next\.js 15/],
  ["App Router", /App Router/],
  ["React 19", /React 19/],
  ["SQLite", /SQLite/],
  ["better-sqlite3", /better-sqlite3/],
  ["Turso or libSQL", /Turso\/libSQL|Turso|libSQL/],
  ["raw SQL migrations", /raw SQL|SQL file|src\/db\/schema/],
  ["migration naming", /NNNN_short_description\.sql/],
  ["foreign keys pragma", /PRAGMA foreign_keys = ON/],
  ["WAL pragma", /PRAGMA journal_mode = WAL/],
  ["busy timeout pragma", /PRAGMA busy_timeout = 5000/],
  ["parameterized SQL", /parameterized statements/],
  ["tenant scoping", /tenant|workspace_id/],
  ["Server Actions", /Server Actions/],
  ["Route Handlers", /Route Handlers/],
  ["Zod validation", /Zod/],
  ["auth guidance", /authorization|requireWorkspaceRole|requireUser/],
  ["test guidance", /Vitest|Playwright/],
  ["package scripts", /"db:migrate"/],
  ["greenfield usable", /greenfield/],
];

const missing = [];
for (const [name, pattern] of checks) {
  if (!pattern.test(text)) {
    missing.push(name);
  }
}

const reasonCount = (text.match(/\bReason:/g) ?? []).length;
if (reasonCount < 24) {
  missing.push(`at least 24 explicit Reason statements, found ${reasonCount}`);
}

const antiPatternCount = (text.match(/^- Do not /gm) ?? []).length;
if (antiPatternCount < 10) {
  missing.push(`at least 10 anti-patterns, found ${antiPatternCount}`);
}

const commandCount = (text.match(/^pnpm /gm) ?? []).length;
if (commandCount < 8) {
  missing.push(`at least 8 dev commands, found ${commandCount}`);
}

if (missing.length > 0) {
  console.error("template validation failed:");
  for (const item of missing) {
    console.error(`- ${item}`);
  }
  process.exit(1);
}

console.log("template validation passed");
console.log(`reason statements: ${reasonCount}`);
console.log(`anti-patterns: ${antiPatternCount}`);
console.log(`dev commands: ${commandCount}`);
