import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

import {
  analyze,
  getPatchLines,
  parseArgs,
  parsePullRequestUrl,
  toMarkdown
} from "../bin/claude-review.mjs";

const execFileAsync = promisify(execFile);

const root = new URL("..", import.meta.url);
const cli = new URL("../bin/claude-review.mjs", import.meta.url);

{
  const { stdout } = await execFileAsync("node", [cli.pathname, "--help"], {
    cwd: root.pathname
  });
  assert.match(stdout, /claude-review 0\.1\.0/);
  assert.match(stdout, /--pr <url>/);
}

{
  const { stdout } = await execFileAsync("node", [cli.pathname, "--version"], {
    cwd: root.pathname
  });
  assert.equal(stdout.trim(), "0.1.0");
}

{
  const args = parseArgs(["--pr", "https://github.com/a/b/pull/1", "--format", "json"]);
  assert.equal(args.pr, "https://github.com/a/b/pull/1");
  assert.equal(args.format, "json");
}

{
  const ref = parsePullRequestUrl("https://github.com/owner/repo/pull/123");
  assert.deepEqual(ref, {
    owner: "owner",
    repo: "repo",
    number: 123,
    url: "https://github.com/owner/repo/pull/123"
  });
}

{
  const files = [
    {
      filename: "src/app.js",
      additions: 2,
      deletions: 0,
      status: "modified",
      patch: "@@ -1,1 +1,2 @@\n+const token = \"abc123456789abcdef\";\n+console.log(token);"
    }
  ];
  const patchInfo = getPatchLines(files, 100);
  const review = analyze(
    { owner: "owner", repo: "repo", number: 1, url: "https://github.com/owner/repo/pull/1" },
    { title: "Demo", user: { login: "alice" }, state: "open", base: { ref: "main" }, head: { ref: "feature" } },
    files,
    patchInfo
  );
  const markdown = toMarkdown(review);

  assert.equal(review.confidence, "Medium");
  assert.match(markdown, /### Summary of Changes/);
  assert.match(markdown, /Security-sensitive addition detected/);
  assert.match(markdown, /Debug logging/);
}

console.log("claude-review tests passed");
