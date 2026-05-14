#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const workflowPath = path.join(
  process.cwd(),
  "workflows",
  "n8n-weekly-github-dev-summary",
  "workflow.json",
);

const workflow = JSON.parse(fs.readFileSync(workflowPath, "utf8"));
const nodes = workflow.nodes ?? [];
const nodeNames = new Set(nodes.map((node) => node.name));
const failures = [];

function assert(condition, message) {
  if (!condition) failures.push(message);
}

function node(name) {
  return nodes.find((candidate) => candidate.name === name);
}

assert(workflow.name, "workflow has a name");
assert(nodes.length >= 10, "workflow includes the expected node set");

const schedule = node("Weekly Friday 5pm");
assert(schedule?.type === "n8n-nodes-base.scheduleTrigger", "weekly schedule node exists");
const interval = schedule?.parameters?.rule?.interval?.[0];
assert(interval?.field === "weeks", "schedule interval is weekly");
assert(interval?.triggerAtDay?.includes(5), "schedule runs on Friday");
assert(interval?.triggerAtHour === 17, "schedule runs at 17:00");

assert(node("Fetch Commits")?.parameters?.url?.includes("/commits?"), "commits endpoint is present");
assert(node("Fetch Closed Issues")?.parameters?.url?.includes("is:issue+closed:"), "closed issues search is present");
assert(node("Fetch Merged PRs")?.parameters?.url?.includes("is:pr+is:merged"), "merged PR search is present");

const claudeBody = node("Call Claude Summary")?.parameters?.jsonBody ?? "";
assert(claudeBody.includes("claude-sonnet-4-20250514"), "Claude model is claude-sonnet-4-20250514");
assert(claudeBody.includes("SUMMARY_LANGUAGE") || claudeBody.includes("summaryLanguage"), "language variable is used");

const configSource = node("Build Config")?.parameters?.jsCode ?? "";
for (const variable of ["GITHUB_OWNER", "GITHUB_REPO", "DESTINATION_MODE", "DESTINATION_URL", "SUMMARY_LANGUAGE"]) {
  assert(configSource.includes(variable), `${variable} is configurable`);
}

assert(node("Send Email")?.type === "n8n-nodes-base.emailSend", "email delivery branch exists");
assert(node("Send Webhook")?.type === "n8n-nodes-base.httpRequest", "webhook delivery branch exists");

for (const [source, groups] of Object.entries(workflow.connections ?? {})) {
  assert(nodeNames.has(source), `connection source exists: ${source}`);
  for (const outputs of Object.values(groups)) {
    for (const output of outputs) {
      for (const edge of output) {
        assert(nodeNames.has(edge.node), `connection target exists: ${source} -> ${edge.node}`);
      }
    }
  }
}

if (failures.length > 0) {
  console.error("Workflow validation failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("Workflow validation passed:");
console.log(`- nodes: ${nodes.length}`);
console.log("- schedule: weekly Friday 17:00");
console.log("- GitHub sources: commits, closed issues, merged PRs");
console.log("- Claude model: claude-sonnet-4-20250514");
console.log("- delivery: email or webhook");
console.log("- required variables: GITHUB_OWNER, GITHUB_REPO, DESTINATION_MODE, DESTINATION_URL, SUMMARY_LANGUAGE");
