#!/usr/bin/env node
/**
 * Validates toolchain env required to run template CI locally or in GitHub Actions.
 */
import { execSync } from "node:child_process";

const required = [
  { name: "node", check: () => execSync("node --version", { encoding: "utf8" }).trim() },
  { name: "bash", check: () => execSync("bash --version", { encoding: "utf8" }).split("\n")[0] },
  { name: "git", check: () => execSync("git --version", { encoding: "utf8" }).trim() },
];

for (const tool of required) {
  try {
    tool.check();
  } catch {
    console.error(`env-check failed: ${tool.name} is required but not available on PATH`);
    process.exit(1);
  }
}

console.log("env-check passed: node, bash, and git are available");
