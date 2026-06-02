import fs from "node:fs";
import vm from "node:vm";

const workflowPath = new URL("./weekly-board-report.workflow.json", import.meta.url);
const workflow = JSON.parse(fs.readFileSync(workflowPath, "utf8"));

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const nodes = new Map(workflow.nodes.map((node) => [node.name, node]));
const requiredNodes = [
  "Friday 5pm Schedule",
  "Collect GitHub Activity",
  "Build Claude Board Brief",
  "Generate Claude Summary",
  "Send Discord Board Report"
];

for (const name of requiredNodes) {
  assert(nodes.has(name), `Missing node: ${name}`);
}

const schedule = nodes.get("Friday 5pm Schedule");
const cron = schedule.parameters.rule.interval[0].expression;
assert(cron === "0 17 * * 5", `Unexpected cron expression: ${cron}`);

const claudeNode = nodes.get("Generate Claude Summary");
assert(claudeNode.parameters.url === "={{$json.anthropicMessagesUrl}}", "Claude endpoint must be configurable");
assert(JSON.stringify(workflow).includes("claude-sonnet-4-20250514"), "Claude model is missing");

const discordNode = nodes.get("Send Discord Board Report");
assert(discordNode.parameters.url === "={{$json.discordWebhookUrl}}", "Discord webhook must be configurable");

for (const node of workflow.nodes) {
  if (node.type === "n8n-nodes-base.code") {
    new vm.Script(`(async () => {\n${node.parameters.jsCode}\n})`, { filename: `${node.name}.js` });
  }
}

console.log(JSON.stringify({
  ok: true,
  workflow: workflow.name,
  nodes: workflow.nodes.length,
  codeNodesCompiled: workflow.nodes.filter((node) => node.type === "n8n-nodes-base.code").length,
  cron,
  model: "claude-sonnet-4-20250514"
}, null, 2));
