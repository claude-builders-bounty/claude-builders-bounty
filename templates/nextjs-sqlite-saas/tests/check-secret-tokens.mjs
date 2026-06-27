#!/usr/bin/env node
/**
 * CI secret-token protection — ensures workflow files and template sources never
 * embed or hard-code secrets. All credentials must use process.env or env.* parsing.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..", "..", "..");
const templateRoot = join(__dirname, "..");
const workflowDir = join(repoRoot, ".github/workflows");

const failures = [];

function scanWorkflow(filename, content) {
  const checks = [
    { pattern: /\$\{\{\s*secrets\./, message: "must not reference ${{ secrets.* }}" },
    { pattern: /secrets:\s*\n\s*\w/, message: "must not declare job-level secrets" },
    { pattern: /UPSTREAM_STATUS_TOKEN|GITHUB_TOKEN\s*:/, message: "must not embed privileged tokens" },
    { pattern: /github-script/, message: "must not use github-script (requires elevated permissions)" },
    {
      pattern: /permissions:[\s\S]*\b(write|id-token|packages|deployments|security-events)\b/,
      message: "must not grant write or token scopes",
    },
  ];
  for (const { pattern, message } of checks) {
    if (pattern.test(content)) {
      failures.push(`${filename}: ${message}`);
    }
  }
}

for (const filename of readdirSync(workflowDir).filter((name) => name.endsWith(".yml"))) {
  scanWorkflow(filename, readFileSync(join(workflowDir, filename), "utf8"));
}

const templateWorkflow = readFileSync(
  join(workflowDir, "test-nextjs-sqlite-template.yml"),
  "utf8",
);
if (!/permissions:\s*\n\s*contents:\s*read/.test(templateWorkflow)) {
  failures.push("test-nextjs-sqlite-template.yml: must declare contents: read permission");
}
if (!templateWorkflow.includes("check-secret-tokens.mjs")) {
  failures.push("test-nextjs-sqlite-template.yml: must run check-secret-tokens.mjs");
}
if (!templateWorkflow.includes("::add-mask::") || !templateWorkflow.includes("SESSION_SECRET")) {
  failures.push("test-nextjs-sqlite-template.yml: must mask SESSION_SECRET in CI logs");
}
if (!templateWorkflow.includes("secret-scanner")) {
  failures.push("test-nextjs-sqlite-template.yml: must run secret-scanner to block secret exposure");
}
if (!templateWorkflow.includes("detect_secrets_version: '1.5.0'")) {
  failures.push(
    "test-nextjs-sqlite-template.yml: must pin detect_secrets_version to 1.5.0 (matches .secrets.baseline)",
  );
}
if (
  !templateWorkflow.includes("Run component tests") ||
  !templateWorkflow.includes("tests/components/")
) {
  failures.push("test-nextjs-sqlite-template.yml: must run component tests explicitly");
}
if (
  !templateWorkflow.includes("file-backed SQLite") ||
  !templateWorkflow.includes("file:./.cache/ci-sqlite")
) {
  failures.push("test-nextjs-sqlite-template.yml: must run migration tests against file-backed SQLite");
}

const hardcodedSecretPatterns = [
  {
    pattern: /SESSION_SECRET\s*[:=]\s*['"](?!\.{3}|test-session)[^'"]{8,}['"]/,
    message: "hardcoded SESSION_SECRET — use process.env.SESSION_SECRET",
  },
  {
    pattern: /DATABASE_URL\s*[:=]\s*['"](?:file:|libsql:|postgres:|mysql:)[^'"]+['"]/,
    message: "hardcoded DATABASE_URL — use process.env.DATABASE_URL",
  },
  {
    pattern: /\b(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['"][^'"]{12,}['"]/i,
    message: "hardcoded API key or token — use environment variables",
  },
  {
    pattern: /\b(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|xox[baprs]-[a-zA-Z0-9-]{10,})\b/,
    message: "embedded provider API key pattern detected",
  },
];

const allowedSourceDirs = [
  join(templateRoot, "reference", "src"),
  join(templateRoot, "reference", "scripts"),
];

function collectSourceFiles(dir, files = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      collectSourceFiles(full, files);
    } else if (/\.(ts|tsx|js|mjs)$/.test(name)) {
      files.push(full);
    }
  }
  return files;
}

for (const dir of allowedSourceDirs) {
  for (const filePath of collectSourceFiles(dir)) {
    const content = readFileSync(filePath, "utf8");
    const rel = relative(templateRoot, filePath);
    for (const { pattern, message } of hardcodedSecretPatterns) {
      if (pattern.test(content)) {
        failures.push(`template/${rel}: ${message}`);
      }
    }
    if (
      /SESSION_SECRET|DATABASE_URL|STRIPE_|WEBHOOK_SECRET/.test(content) &&
      !/process\.env\./.test(content) &&
      !/env\.(SESSION_SECRET|DATABASE_URL)/.test(content) &&
      !content.includes("z.string()") &&
      !content.includes("z.object")
    ) {
      failures.push(
        `template/${rel}: secret env vars must be read via process.env or env.* — never hard-coded`,
      );
    }
  }
}

const claudeMd = readFileSync(join(templateRoot, "CLAUDE.md"), "utf8");
const claudeCodeBlocks = [...claudeMd.matchAll(/```(?:ts|tsx|bash|sh)?\n([\s\S]*?)```/g)].map(
  (match) => match[1],
);
for (const [index, block] of claudeCodeBlocks.entries()) {
  if (block.includes("# .env.local") || block.includes('SESSION_SECRET="..."')) {
    continue;
  }
  for (const { pattern, message } of hardcodedSecretPatterns) {
    if (pattern.test(block)) {
      failures.push(`CLAUDE.md code block ${index + 1}: ${message}`);
    }
  }
}

// Peer-review: shared env validation module and reference env script wiring.
const envValidationUtils = readFileSync(
  join(repoRoot, "scripts/env-validation-utils.mjs"),
  "utf8",
);
if (!envValidationUtils.includes("isStrongSessionSecret") || !envValidationUtils.includes("length < 32")) {
  failures.push(
    "scripts/env-validation-utils.mjs: must reject SESSION_SECRET shorter than 32 characters",
  );
}
if (!envValidationUtils.includes("NEXT_PUBLIC_APP_URL") || !envValidationUtils.includes("isValidAppUrl")) {
  failures.push(
    "scripts/env-validation-utils.mjs: must validate NEXT_PUBLIC_APP_URL as http(s) URL",
  );
}
const validateReferenceEnv = readFileSync(
  join(repoRoot, "scripts/validate-reference-env.mjs"),
  "utf8",
);
if (!validateReferenceEnv.includes("env-validation-utils.mjs")) {
  failures.push(
    "scripts/validate-reference-env.mjs: must import shared env-validation-utils.mjs",
  );
}
if (!validateReferenceEnv.includes("NEXT_PUBLIC_APP_URL")) {
  failures.push(
    "scripts/validate-reference-env.mjs: must validate NEXT_PUBLIC_APP_URL alongside DATABASE_URL and SESSION_SECRET",
  );
}

const referenceEnvTs = readFileSync(
  join(templateRoot, "reference", "src", "lib", "env.ts"),
  "utf8",
);
if (!/SESSION_SECRET:\s*z\.string\(\)\.min\(32\)/.test(referenceEnvTs)) {
  failures.push("reference/src/lib/env.ts: SESSION_SECRET must use z.string().min(32)");
}

const weakSessionSecretPattern =
  /SESSION_SECRET\s*[:=]\s*['"]([^'"]{1,31})['"]/;
for (const dir of allowedSourceDirs) {
  for (const filePath of collectSourceFiles(dir)) {
    const content = readFileSync(filePath, "utf8");
    const rel = relative(templateRoot, filePath);
    const match = content.match(weakSessionSecretPattern);
    if (match) {
      failures.push(
        `template/${rel}: SESSION_SECRET value "${match[1]}" is shorter than 32 characters`,
      );
    }
  }
}

if (failures.length) {
  console.error(`FAILED secret token protection:\n- ${failures.join("\n- ")}`);
  process.exit(1);
}

console.log("OK: secret token protection checks passed");
