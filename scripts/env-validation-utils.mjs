/**
 * Shared env validation helpers for reference app CI and local test harnesses.
 * Imported by scripts/validate-reference-env.mjs and security audit checks.
 */

export const WEAK_SESSION_SECRETS = new Set(["changeme", "secret", "password"]);

export function isStrongSessionSecret(value) {
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

export function isValidDatabaseUrl(value) {
  return (
    value.startsWith("file:") || value.startsWith("libsql:") || value === ":memory:"
  );
}

export function isValidAppUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export function validateEnvVar(name, rawValue, { validate, hint }) {
  const value = rawValue?.trim() ?? "";
  if (!value || !validate(value)) {
    return `${name} is missing or invalid (expected: ${hint})`;
  }
  return null;
}

export const REQUIRED_REFERENCE_ENV = [
  {
    name: "DATABASE_URL",
    validate: isValidDatabaseUrl,
    hint: "file:./data/app.db, libsql://..., or :memory:",
  },
  {
    name: "SESSION_SECRET",
    validate: isStrongSessionSecret,
    hint: "32+ chars with mixed character classes (not all one character or a known weak value)",
  },
  {
    name: "NEXT_PUBLIC_APP_URL",
    validate: isValidAppUrl,
    hint: "http:// or https:// origin URL (matches env.ts z.string().url())",
  },
];

export function validateRequiredEnv(required = REQUIRED_REFERENCE_ENV, env = process.env) {
  const failures = [];
  for (const spec of required) {
    const message = validateEnvVar(spec.name, env[spec.name], spec);
    if (message) {
      failures.push(message);
    }
  }
  return failures;
}
