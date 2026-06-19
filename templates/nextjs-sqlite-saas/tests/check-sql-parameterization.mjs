#!/usr/bin/env node
/**
 * Static SQL audit — query modules and scripts must use prepared statements,
 * never string concatenation or template interpolation in SQL.
 * Peer-review requirement for PR #2529 / issue #2.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const referenceRoot = join(__dirname, "..", "reference");

const failures = [];

function auditSqlFile(path, label) {
  const content = readFileSync(path, "utf8");

  if (/`[^`]*\$\{/.test(content)) {
    failures.push(`${label}: SQL must not use template literal interpolation`);
  }
  if (/\.exec\s*\(\s*[`'"][^`'"]*\+/.test(content)) {
    failures.push(`${label}: must not concatenate dynamic SQL for db.exec`);
  }
  if (/\.prepare\s*\(\s*[`'"][^`'"]*\+/.test(content)) {
    failures.push(`${label}: must not concatenate dynamic SQL for db.prepare`);
  }
}

const queriesDir = join(referenceRoot, "src", "db", "queries");
if (!statSync(queriesDir).isDirectory()) {
  console.error(`FAILED SQL audit: missing queries directory ${queriesDir}`);
  process.exit(1);
}

for (const filename of readdirSync(queriesDir).filter((name) => name.endsWith(".ts"))) {
  const path = join(queriesDir, filename);
  const label = `src/db/queries/${filename}`;
  const content = readFileSync(path, "utf8");
  if (!content.includes(".prepare(")) {
    failures.push(`${label}: query module must use db.prepare for all SQL`);
  }
  auditSqlFile(path, label);
}

const scriptsDir = join(referenceRoot, "scripts");
if (statSync(scriptsDir).isDirectory()) {
  for (const filename of readdirSync(scriptsDir).filter((name) => name.endsWith(".ts"))) {
    const path = join(scriptsDir, filename);
    const content = readFileSync(path, "utf8");
    if (!/\.prepare\s*\(|db\.exec\s*\(/.test(content)) {
      continue;
    }
    auditSqlFile(path, `scripts/${filename}`);
  }
}

if (failures.length) {
  console.error(`FAILED SQL parameterization audit:\n- ${failures.join("\n- ")}`);
  process.exit(1);
}

console.log("OK: SQL parameterization audit passed");
