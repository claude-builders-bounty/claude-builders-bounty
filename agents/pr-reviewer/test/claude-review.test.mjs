import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const cli = resolve(__dirname, "..", "bin", "claude-review.mjs");

const result = spawnSync(
  process.execPath,
  [cli, "--help"],
  { encoding: "utf8", maxBuffer: 1024 * 1024 * 8 }
);

assert.equal(result.status, 0, result.stderr);
assert.match(result.stdout, /claude-review --pr/);
assert.match(result.stdout, /--engine auto\|claude\|local/);
assert.match(result.stdout, /--max-budget-usd/);

console.log("claude-review offline CLI smoke test passed");
