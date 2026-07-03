#!/usr/bin/env node
/**
 * Validates required env vars for the reference app test harness.
 * Peer-review requirement: DATABASE_URL, SESSION_SECRET, and NEXT_PUBLIC_APP_URL
 * must meet criteria before Vitest (not merely be present).
 */
import {
  REQUIRED_REFERENCE_ENV,
  validateRequiredEnv,
} from "./env-validation-utils.mjs";

const failures = validateRequiredEnv(REQUIRED_REFERENCE_ENV, process.env);

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

console.log(
  "OK: reference env vars validated (DATABASE_URL, SESSION_SECRET, NEXT_PUBLIC_APP_URL)",
);
