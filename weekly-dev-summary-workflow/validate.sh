#!/usr/bin/env bash
set -euo pipefail

workflow="weekly-dev-summary-workflow/workflow.json"

if command -v jq >/dev/null 2>&1; then
  jq -e '.name == "Weekly Dev Summary with Claude"' "$workflow" >/dev/null
  jq -e '.nodes[] | select(.type == "n8n-nodes-base.scheduleTrigger" and .name == "Weekly Friday 5pm")' "$workflow" >/dev/null
  jq -e '.nodes[] | select(.name == "Fetch Commits" and (.parameters.url | contains("/commits")))' "$workflow" >/dev/null
  jq -e '.nodes[] | select(.name == "Fetch Closed Issues" and (.parameters.queryParameters.parameters[]?.value | tostring | contains("type:issue")))' "$workflow" >/dev/null
  jq -e '.nodes[] | select(.name == "Fetch Merged Pull Requests" and (.parameters.queryParameters.parameters[]?.value | tostring | contains("type:pr is:merged")))' "$workflow" >/dev/null
  jq -e '.nodes[] | select(.name == "Claude Narrative Summary" and (.parameters.jsonBody | contains("claude-sonnet-4-20250514")))' "$workflow" >/dev/null
  jq -e '.nodes[] | select(.name == "Send Discord Webhook")' "$workflow" >/dev/null
  jq -e '.nodes[] | select(.name == "Configuration" and (.parameters.assignments.assignments | map(.name) | index("githubOwner") and index("githubRepo") and index("destinationWebhookUrl") and index("summaryLanguage")))' "$workflow" >/dev/null
else
  node <<'NODE'
const fs = require("fs");
const workflow = JSON.parse(fs.readFileSync("weekly-dev-summary-workflow/workflow.json", "utf8"));
const nodes = workflow.nodes || [];
const findNode = (name) => nodes.find((node) => node.name === name);
const assert = (condition, message) => {
  if (!condition) {
    throw new Error(message);
  }
};

assert(workflow.name === "Weekly Dev Summary with Claude", "workflow name mismatch");
assert(
  nodes.some((node) => node.type === "n8n-nodes-base.scheduleTrigger" && node.name === "Weekly Friday 5pm"),
  "missing weekly schedule trigger",
);
assert(findNode("Fetch Commits")?.parameters?.url?.includes("/commits"), "missing commits fetch");
assert(
  findNode("Fetch Closed Issues")?.parameters?.queryParameters?.parameters?.some((param) =>
    String(param.value).includes("type:issue"),
  ),
  "missing closed issues query",
);
assert(
  findNode("Fetch Merged Pull Requests")?.parameters?.queryParameters?.parameters?.some((param) =>
    String(param.value).includes("type:pr is:merged"),
  ),
  "missing merged PR query",
);
assert(
  findNode("Claude Narrative Summary")?.parameters?.jsonBody?.includes("claude-sonnet-4-20250514"),
  "missing Claude model",
);
assert(findNode("Send Discord Webhook"), "missing Discord webhook node");

const assignmentNames =
  findNode("Configuration")?.parameters?.assignments?.assignments?.map((assignment) => assignment.name) || [];
for (const name of ["githubOwner", "githubRepo", "destinationWebhookUrl", "summaryLanguage"]) {
  assert(assignmentNames.includes(name), `missing configuration assignment: ${name}`);
}
NODE
fi

echo "workflow.json passed structural validation"
