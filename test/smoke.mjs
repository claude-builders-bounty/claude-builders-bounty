import { spawn } from "node:child_process";

const child = spawn(process.execPath, [
  "./bin/claude-review.mjs",
  "--help"
], {
  cwd: new URL("..", import.meta.url),
  stdio: ["ignore", "pipe", "pipe"]
});

let stderr = "";
let stdout = "";
child.stdout.on("data", (chunk) => {
  stdout += chunk;
});
child.stderr.on("data", (chunk) => {
  stderr += chunk;
});

const code = await new Promise((resolve) => child.on("close", resolve));
if (code !== 0) throw new Error(`smoke command failed: ${stderr}`);

for (const text of ["Usage:", "--pr <url>", "ANTHROPIC_API_KEY", "GITHUB_TOKEN"]) {
  if (!stdout.includes(text)) throw new Error(`missing help text: ${text}`);
}
