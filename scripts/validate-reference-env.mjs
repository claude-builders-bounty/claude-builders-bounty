#!/usr/bin/env node
/**
 * Validates required env vars for the reference app test harness.
 * Peer-review requirement: DATABASE_URL and SESSION_SECRET values must meet criteria
 * before Vitest (not merely be present).
 */

const WEAK_SESSION_SECRETS = new Set([
  "changeme",
  "secret",
  "password",
]);

function isStrongSessionSecret(value) {
  if (value.length < 32) {
    return false;
  }
  if (/^(.)\1+$/.test(value)) {
    return false;
  }
  if (WEAK_SESSION_SECRETS.has(value.toLowerCase())) {
    return false;
  }
  const classes = [
    /[a-z]/,
    /[A-Z]/,
    /[0-9]/,
    /[^a-zA-Z0-9]/,
  ].filter((pattern) => pattern.test(value)).length;
  return classes >= 2;
}

const REQUIRED = [
  {
    name: "DATABASE_URL",
    validate: (value) =>
      value.startsWith("file:") || value.startsWith("libsql:") || value === ":memory:",
    hint: "file:./data/app.db, libsql://..., or :memory:",
  },
  {
    name: "SESSION_SECRET",
    validate: isStrongSessionSecret,
    hint: "32+ chars with mixed character classes (not all one character or a known weak value)",
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
