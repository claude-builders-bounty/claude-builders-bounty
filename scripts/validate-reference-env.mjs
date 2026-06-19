#!/usr/bin/env node
/**
 * Validates required env vars for the reference app test harness.
 * Peer-review requirement: DATABASE_URL and SESSION_SECRET must be set before Vitest.
 */
import { spawnSync } from "node:child_process";

const REQUIRED = [
  {
    name: "DATABASE_URL",
    validate: (value) =>
      value.startsWith("file:") || value.startsWith("libsql:") || value === ":memory:",
    hint: "file:./data/app.db, libsql://..., or :memory:",
  },
  {
    name: "SESSION_SECRET",
    validate: (value) => value.length >= 32,
    hint: "32+ random bytes",
  },
];

const failures = [];

for (const { name, validate, hint } of REQUIRED) {
  const value = process.env[name]?.trim() ?? "";
  if (!value || !validate(value)) {
    failures.push(`${name} is missing or invalid (expected: ${hint})`);
  }
}

if (failures.length) {
  console.error("validate-reference-env failed:");
  for (const message of failures) {
    console.error(`  - ${message}`);
  }
  console.error(
    "Set env vars in templates/nextjs-sqlite-saas/reference/tests/setup.ts or export before running Vitest.",
  );
  process.exit(1);
}

console.log("OK: reference env vars validated (DATABASE_URL, SESSION_SECRET)");
