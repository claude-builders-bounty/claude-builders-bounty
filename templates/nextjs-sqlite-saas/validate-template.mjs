#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const templatePath = join(here, "CLAUDE.md");
const template = readFileSync(templatePath, "utf8");
const smokeProtocolPath = join(here, "verification", "claude-code-greenfield-smoke.md");
const smokeProtocol = readFileSync(smokeProtocolPath, "utf8");

const requiredHeadings = [
  "# CLAUDE.md - Next.js 15 + SQLite SaaS",
  "## Stack And Versions",
  "## Project Structure",
  "## Naming Conventions",
  "## Environment Rules",
  "## Database And Migration Rules",
  "## Data Access Pattern",
  "## Auth And Authorization",
  "## Server And Client Component Rules",
  "## Server Actions",
  "## Route Handlers And APIs",
  "## UI And Product Patterns",
  "## Error Handling",
  "## Testing Rules",
  "## Commands",
  "## Pull Request Rules",
  "## What We Do Not Do",
  "## Agent Workflow",
  "## Greenfield Claude Code Smoke Test",
];

const requiredTerms = [
  "Next.js 15",
  "SQLite",
  "better-sqlite3",
  "Turso",
  "Drizzle",
  "middleware.ts",
  "Server Actions",
  "Route Handlers",
  "Zod",
  "migrations",
  "greenfield",
  "Claude Code",
  "Node.js",
  "Node.js 22",
  "15.5.28",
  "@types/better-sqlite3",
  "Edge Runtime",
  "persistent writable volume",
  "one writer",
  "busy timeout",
  "requireCurrentUser()",
  "searchParams",
];

const errors = [];

for (const heading of requiredHeadings) {
  if (!template.includes(heading)) {
    errors.push(`Missing heading: ${heading}`);
  }
}

for (const term of requiredTerms) {
  if (!new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i").test(template)) {
    errors.push(`Missing required term: ${term}`);
  }
}

const reasonCount = (template.match(/\bReason:/g) || []).length;
if (reasonCount < 40) {
  errors.push(`Expected at least 40 reasoned rules, found ${reasonCount}`);
}

const numberedSmokeSteps = (smokeProtocol.match(/^\d+\.\s+/gm) || []).length;
if (numberedSmokeSteps < 4) {
  errors.push(`Expected at least 4 numbered real Claude Code smoke-test setup steps, found ${numberedSmokeSteps}`);
}

if (!/Status: Protocol only[\s\S]*NOT run/i.test(smokeProtocol)) {
  errors.push("Smoke-test protocol must clearly distinguish an unrun procedure from execution evidence");
}

for (const term of ["Exact first prompt", "Pass only if", "Fail if", "claude --version", "Do not edit files"]) {
  if (!smokeProtocol.includes(term)) {
    errors.push(`Smoke-test protocol missing: ${term}`);
  }
}

const antiPatternSection = template.split("## What We Do Not Do")[1]?.split("## Agent Workflow")[0] || "";
const antiPatternCount = (antiPatternSection.match(/^- Do not /gm) || []).length;
if (antiPatternCount < 9) {
  errors.push(`Expected at least 9 explicit anti-pattern rows, found ${antiPatternCount}`);
}

const codeFenceCount = (template.match(/^```/gm) || []).length;
if (codeFenceCount % 2 !== 0) {
  errors.push(`Unbalanced Markdown code fences: ${codeFenceCount}`);
}

if (!/Expected behavior:[\s\S]*Claude Code[\s\S]*(?:without asking|should not ask)/i.test(template)) {
  errors.push("Missing explicit expected Claude Code greenfield behavior");
}

if (!/middleware\.ts[\s\S]*auth redirects[\s\S]*coarse guards/i.test(template)) {
  errors.push("Missing middleware scope guidance");
}

if (!/native Node\.js driver[\s\S]*Edge Runtime[\s\S]*client code/i.test(template)) {
  errors.push("Missing better-sqlite3 Node-only runtime boundary");
}

if (!/pin `next`[^\n]*15\.5\.28/i.test(template)) {
  errors.push("Missing patched Next.js 15.5.28 minimum-version rule");
}

if (!/better-sqlite3[^\n]*@types\/better-sqlite3[^\n]*devDependency/i.test(template)) {
  errors.push("Missing conditional @types/better-sqlite3 devDependency rule");
}

if (!/create-next-app@15\.5\.28\b/.test(smokeProtocol)) {
  errors.push("Smoke-test protocol must use the patched Next.js 15.5.28 starter");
}

if (!/await requireCurrentUser\(\)[\s\S]*ownerId: actor\.id/.test(template)) {
  errors.push("Server Action example must derive owner identity from the trusted server auth boundary");
}

if (errors.length > 0) {
  console.error("CLAUDE.md template validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`CLAUDE.md template contract passed: ${requiredHeadings.length} headings, ${reasonCount} reasoned rules, ${antiPatternCount} anti-patterns, ${numberedSmokeSteps} documented manual setup steps. Claude Code execution is not performed by this check.`);
