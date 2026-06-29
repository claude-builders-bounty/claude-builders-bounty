#!/usr/bin/env node
const { spawnSync } = require("child_process");
const path = require("path");

const script = path.join(__dirname, "..", "claude_review.py");
const py = process.env.PYTHON || "python3";
const result = spawnSync(py, [script, ...process.argv.slice(2)], {
  stdio: "inherit",
  shell: process.platform === "win32",
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);
