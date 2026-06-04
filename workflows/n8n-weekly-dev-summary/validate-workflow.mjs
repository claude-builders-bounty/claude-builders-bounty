import { readFile } from "node:fs/promises";

const workflow = JSON.parse(await readFile(new URL("./workflow.json", import.meta.url), "utf8"));
const requiredNodes = [
  "Weekly Friday Trigger",
  "Fetch Commits",
  "Fetch Closed Issues",
  "Fetch Closed PRs",
  "Call Claude Sonnet 4",
  "Send Discord Webhook"
];

const nodeNames = new Set(workflow.nodes.map((node) => node.name));
const missing = requiredNodes.filter((name) => !nodeNames.has(name));
if (missing.length) {
  console.error(JSON.stringify({ ok: false, missing }, null, 2));
  process.exit(1);
}

const claudeNode = workflow.nodes.find((node) => node.name === "Call Claude Sonnet 4");
const workflowText = JSON.stringify(workflow);
const checks = {
  importableJson: Boolean(workflow.name && Array.isArray(workflow.nodes) && workflow.connections),
  weeklyCron: workflowText.includes("triggerAtDay") && workflowText.includes("triggerAtHour"),
  githubCommits: workflowText.includes("/commits"),
  closedIssues: workflowText.includes("/issues"),
  mergedPRs: workflowText.includes("/pulls") && workflowText.includes("merged_at"),
  claudeModel: workflowText.includes("claude-sonnet-4-20250514"),
  discordWebhook: workflowText.includes("DESTINATION_WEBHOOK_URL"),
  configurableVariables: ["GITHUB_REPO", "GITHUB_TOKEN", "ANTHROPIC_API_KEY", "SUMMARY_LANGUAGE"].every((key) => workflowText.includes(key)),
  claudeEndpoint: claudeNode?.parameters?.url === "https://api.anthropic.com/v1/messages"
};

const failed = Object.entries(checks).filter(([, value]) => !value).map(([key]) => key);
if (failed.length) {
  console.error(JSON.stringify({ ok: false, failed }, null, 2));
  process.exit(1);
}

console.log(
  JSON.stringify(
    {
      ok: true,
      workflow: workflow.name,
      nodes: workflow.nodes.length,
      requiredNodes,
      checks
    },
    null,
    2
  )
);
