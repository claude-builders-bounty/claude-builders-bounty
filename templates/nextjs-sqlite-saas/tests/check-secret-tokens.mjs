#!/usr/bin/env node
/**
 * CI secret-token protection — ensures workflow files never embed or request secrets.
 * Peer-review requirement for PR #2529 / issue #2.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..", "..", "..");
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

if (failures.length) {
  console.error(`FAILED secret token protection:\n- ${failures.join("\n- ")}`);
  process.exit(1);
}

console.log("OK: secret token protection checks passed");
