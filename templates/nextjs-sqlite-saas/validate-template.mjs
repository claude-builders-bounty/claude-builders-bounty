import { readFileSync } from "node:fs";

const text = readFileSync(new URL("./CLAUDE.md", import.meta.url), "utf8");

const required = [
  "## Stack And Versions",
  "## Folder Structure",
  "## Naming Conventions",
  "## Dev Commands",
  "## SQL And Migration Rules",
  "## Component Patterns",
  "## Anti-Patterns",
  "## Greenfield Smoke Test",
  "Next.js 15",
  "SQLite",
  "better-sqlite3",
  "Turso",
  "Reason:",
];

const missing = required.filter((item) => !text.includes(item));

if (missing.length > 0) {
  console.error(`Missing required template coverage:\n${missing.map((item) => `- ${item}`).join("\n")}`);
  process.exit(1);
}

const reasonCount = text.match(/Reason:/g)?.length ?? 0;
if (reasonCount < 20) {
  console.error(`Expected at least 20 opinionated reasons, found ${reasonCount}.`);
  process.exit(1);
}

console.log(`Template validation passed with ${reasonCount} explicit reasons.`);
