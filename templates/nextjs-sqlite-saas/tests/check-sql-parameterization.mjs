#!/usr/bin/env node
/**
 * Static SQL audit — query modules must use prepared statements, never string concatenation.
 * Peer-review requirement for PR #2529 / issue #2.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const queriesDir = join(__dirname, "..", "reference", "src", "db", "queries");

const failures = [];

if (!statSync(queriesDir).isDirectory()) {
  console.error(`FAILED SQL audit: missing queries directory ${queriesDir}`);
  process.exit(1);
}

for (const filename of readdirSync(queriesDir).filter((name) => name.endsWith(".ts"))) {
  const path = join(queriesDir, filename);
  const content = readFileSync(path, "utf8");

  if (/`[^`]*\$\{/.test(content)) {
    failures.push(`${filename}: SQL must not use template literal interpolation`);
  }
  if (/\.exec\s*\(\s*[`'"][^`'"]*\+/.test(content)) {
    failures.push(`${filename}: must not concatenate dynamic SQL for db.exec`);
  }
  if (/\.prepare\s*\(\s*[`'"][^`'"]*\+/.test(content)) {
    failures.push(`${filename}: must not concatenate dynamic SQL for db.prepare`);
  }
  if (!content.includes(".prepare(")) {
    failures.push(`${filename}: query module must use db.prepare for all SQL`);
  }
}

if (failures.length) {
  console.error(`FAILED SQL parameterization audit:\n- ${failures.join("\n- ")}`);
  process.exit(1);
}

console.log("OK: SQL parameterization audit passed");
