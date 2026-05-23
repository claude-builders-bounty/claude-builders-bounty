import fs from "node:fs";
import assert from "node:assert/strict";

const path = new URL("../workflow.json", import.meta.url);
const workflow = JSON.parse(fs.readFileSync(path, "utf8"));
const nodes = new Map(workflow.nodes.map((node) => [node.name, node]));

for (const name of [
  "Weekly Friday 5 PM",
  "Manual Test Trigger",
  "Build Weekly Window",
  "Fetch GitHub Activity",
  "Compose Claude Prompt",
  "Generate Claude Summary",
  "Format Delivery Payload",
  "Deliver to Discord",
]) {
  assert.ok(nodes.has(name), `missing node: ${name}`);
}

assert.equal(nodes.get("Weekly Friday 5 PM").type, "n8n-nodes-base.scheduleTrigger");
assert.match(JSON.stringify(nodes.get("Weekly Friday 5 PM").parameters), /0 17 \* \* 5/);
assert.equal(nodes.get("Manual Test Trigger").type, "n8n-nodes-base.executeWorkflowTrigger");

const githubActivity = nodes.get("Fetch GitHub Activity");

assert.equal(githubActivity.type, "n8n-nodes-base.code");
assert.match(githubActivity.parameters.jsCode, /api\.github\.com\/repos/);
assert.match(githubActivity.parameters.jsCode, /commits/);
assert.match(githubActivity.parameters.jsCode, /state=closed/);
assert.match(githubActivity.parameters.jsCode, /is:pr is:merged/);
assert.match(githubActivity.parameters.jsCode, /Promise\.all/);

const claude = nodes.get("Generate Claude Summary");
assert.match(JSON.stringify(claude.parameters), /api\.anthropic\.com/);
assert.match(JSON.stringify(claude.parameters), /\/v1\/messages/);
assert.match(JSON.stringify(claude.parameters), /claude-sonnet-4-20250514/);
assert.match(JSON.stringify(claude.parameters), /ANTHROPIC_API_KEY/);

const buildWindow = nodes.get("Build Weekly Window");
assert.match(buildWindow.parameters.jsCode, /GITHUB_REPO/);
assert.match(buildWindow.parameters.jsCode, /SUMMARY_LANGUAGE/);
assert.match(buildWindow.parameters.jsCode, /DELIVERY_TARGET/);

const delivery = nodes.get("Deliver to Discord");
assert.match(JSON.stringify(delivery.parameters), /DISCORD_WEBHOOK_URL/);

assert.ok(workflow.connections["Weekly Friday 5 PM"], "schedule must connect");
assert.ok(workflow.connections["Manual Test Trigger"], "manual test trigger must connect");
assert.ok(workflow.connections["Format Delivery Payload"], "delivery payload must connect");
assert.equal(workflow.active, false, "workflow should import inactive for credential setup");

console.log("workflow validation passed");
