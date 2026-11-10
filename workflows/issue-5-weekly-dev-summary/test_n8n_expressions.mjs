#!/usr/bin/env node
// Offline checks using the actual resolver shipped with n8n 2.32.6.
// This does not execute HTTP requests or establish live workflow acceptance.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const runtimeRoot = process.argv[2];
if (!runtimeRoot) {
  throw new Error("Pass the isolated npm runtime directory containing n8n-workflow@2.32.1.");
}
const requireRuntime = createRequire(resolve(runtimeRoot, "package.json"));
const { Expression } = requireRuntime("n8n-workflow");
const { version } = requireRuntime("n8n-workflow/package.json");
assert.equal(version, "2.32.1", "Use the n8n-workflow version shipped with n8n 2.32.6.");

const here = dirname(fileURLToPath(import.meta.url));
const workflow = JSON.parse(readFileSync(resolve(here, "weekly-github-claude-summary.workflow.json"), "utf8"));
const fixtures = [
  ["ordinary", "Weekly activity: one merged pull request."],
  ["quoted multiline Unicode", 'Title: "Ship onboarding"\nContributor: Renée 🚀\nSecond line.'],
  ["expression-looking repository content", 'Literal data: {{ $env.UNUSED_TEST_SECRET }} and {{ $json.notAField }}'],
  ["backslashes and control characters", "Path C:\\fixture\\project\r\nTabbed\tactivity"],
  ["untrusted mention text", "Quoted activity: <@123456789012345678> <@&234567890123456789> @everyone @here"],
];

for (const [nodeName, inputKey] of [
  ["Generate Claude Summary", "prompt"],
  ["Send Discord Summary", "message"],
]) {
  const node = workflow.nodes.find((candidate) => candidate.name === nodeName);
  assert.ok(node, `Missing ${nodeName}`);
  for (const [fixtureName, text] of fixtures) {
    test(`${nodeName}: ${fixtureName}`, () => {
      assert.equal(node.parameters.method, "POST");
      assert.equal(node.parameters.sendBody, true);
      assert.equal(node.parameters.specifyBody, "json");
      const resolved = new Expression("UTC").resolveSimpleParameterValue(
        node.parameters.jsonBody,
        { $json: { [inputKey]: text } },
      );
      assert.equal(typeof resolved, "object", "JSON body must resolve to an object, not literal $json text.");
      assert.ok(resolved !== null && !Array.isArray(resolved));
      const expected = nodeName === "Generate Claude Summary"
        ? {
            model: "claude-sonnet-4-6",
            max_tokens: 1200,
            temperature: 0.3,
            messages: [{ role: "user", content: text }],
          }
        : { content: text, allowed_mentions: { parse: [] } };
      assert.deepEqual(resolved, expected);
      // n8n's HTTP Request node accepts resolved objects directly; ensure the
      // eventual JSON wire representation preserves every input character.
      assert.deepEqual(JSON.parse(JSON.stringify(resolved)), expected);
    });
  }
}
