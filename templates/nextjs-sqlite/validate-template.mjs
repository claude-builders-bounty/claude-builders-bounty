#!/usr/bin/env node
// Validates that CLAUDE.md meets Bounty #2 acceptance criteria + contains expected sections.
// Run: node templates/nextjs-sqlite/validate-template.mjs
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const p = join(dir, "CLAUDE.md");
if (!existsSync(p)) { console.error("missing CLAUDE.md at", p); process.exit(1); }
const s = readFileSync(p, "utf8");
const checks = [
  ["Stack & versions", /Stack.*Pinned|Stack.*versions/i],
  ["Folder structure", /Folder Structure|Directory.*File Organization/i],
  ["DB migration rules", /migration/i],
  ["Naming conventions", /Naming/i],
  ["Dev commands", /Dev Commands|pnpm dev|pnpm build/i],
  ["Patterns to follow", /Patterns|Server Component|Server Action/i],
  ["Anti-patterns", /Anti-Pattern|What We Don.t Do/i],
  ["Opinionated (has reasons)", /reason:/i],
  ["better-sqlite3", /better-sqlite3/i],
  ["WAL pragma", /journal_mode.*WAL/i],
  ["Drizzle", /drizzle/i],
  ["zod", /zod/i],
];
let bad = 0;
for (const [label, re] of checks) {
  const ok = re.test(s);
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
  if (!ok) bad++;
}
console.log(`\n${bad === 0 ? "All checks passed." : `${bad} check(s) failed.`}  (${s.length} bytes, ${s.split("\n").length} lines)`);
process.exit(bad === 0 ? 0 : 1);
