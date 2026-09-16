import { strict as assert } from "node:assert";
import { readFile } from "node:fs/promises";

const agent = await readFile(new URL("../.claude/agents/pr-reviewer.md", import.meta.url), "utf8");

assert.match(agent, /^---\n/);
assert.match(agent, /\nname: pr-reviewer\n/);
assert.match(agent, /\ndescription: .+pull requests.+structured Markdown/i);
assert.match(agent, /\ntools: Read, WebFetch\n/);
assert.match(agent, /\nmodel: sonnet\n/);
assert.match(agent, /\n---\n\nYou are a focused pull request review subagent\./);
assert.match(agent, /## Output Format/);
assert.match(agent, /## Identified Risks/);
assert.match(agent, /## Improvement Suggestions/);
assert.match(agent, /## Confidence/);
assert.match(agent, /Never post the review externally unless the caller explicitly asks\./);

console.log("subagent.test.mjs ok");

