import { readFileSync } from "node:fs";

const workflowPath = new URL("./weekly-github-claude-summary.json", import.meta.url);
const workflow = JSON.parse(readFileSync(workflowPath, "utf8"));

const requiredNodes = [
  "Weekly Friday 5pm",
  "Collect GitHub Activity",
  "Build Claude Request",
  "Generate Summary with Claude",
  "Format Discord Payload",
  "Send Discord Summary",
];

for (const nodeName of requiredNodes) {
  if (!workflow.nodes.some((node) => node.name === nodeName)) {
    throw new Error(`Missing required node: ${nodeName}`);
  }
}

const workflowText = JSON.stringify(workflow);
for (const required of [
  "GITHUB_REPO",
  "DESTINATION_WEBHOOK_URL",
  "ANTHROPIC_API_KEY",
  "SUMMARY_LANGUAGE",
  "claude-sonnet-4-20250514",
  "https://api.github.com/repos/",
]) {
  if (!workflowText.includes(required)) {
    throw new Error(`Workflow does not reference ${required}`);
  }
}

const edges = [
  ["Weekly Friday 5pm", "Collect GitHub Activity"],
  ["Collect GitHub Activity", "Build Claude Request"],
  ["Build Claude Request", "Generate Summary with Claude"],
  ["Generate Summary with Claude", "Format Discord Payload"],
  ["Format Discord Payload", "Send Discord Summary"],
];

for (const [from, to] of edges) {
  const outbound = workflow.connections[from]?.main?.[0] ?? [];
  if (!outbound.some((edge) => edge.node === to)) {
    throw new Error(`Missing connection: ${from} -> ${to}`);
  }
}

console.log("workflow validation passed");
