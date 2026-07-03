#!/usr/bin/env node
/**
 * Validates toolchain binaries required to run template CI locally or in GitHub Actions.
 *
 * Security: uses spawnSync with a fixed argv whitelist (no shell, no user input,
 * no env-var interpolation). Only `--version` probes are executed.
 */
import { spawnSync } from "node:child_process";

/** @type {ReadonlyArray<{ name: string; argv: readonly string[] }>} */
const REQUIRED_TOOLS = [
  { name: "node", argv: ["node", "--version"] },
  { name: "bash", argv: ["bash", "--version"] },
  { name: "git", argv: ["git", "--version"] },
];

// Minimal environment: PATH only, so NODE_OPTIONS / shell injection cannot alter probes.
const safeEnv = { PATH: process.env.PATH ?? "" };

for (const { name, argv } of REQUIRED_TOOLS) {
  const [command, ...args] = argv;
  const result = spawnSync(command, args, {
    encoding: "utf8",
    shell: false,
    env: safeEnv,
  });

  if (result.error || result.status !== 0) {
    console.error(`env-check failed: ${name} is required but not available on PATH`);
    process.exit(1);
  }
}

console.log("env-check passed: node, bash, and git are available");
