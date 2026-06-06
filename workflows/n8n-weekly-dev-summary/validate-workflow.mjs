import { readFileSync } from "node:fs";

const workflow = JSON.parse(readFileSync(new URL("./workflow.json", import.meta.url), "utf8"));
const readme = readFileSync(new URL("./README.md", import.meta.url), "utf8");
const serialized = JSON.stringify(workflow);

const requiredNodeNames = [
  "Friday 5pm Trigger",
  "Prepare Config",
  "Fetch Commits",
  "Fetch Closed Issues",
  "Fetch Merged PRs",
  "Build Claude Prompt",
  "Generate Summary With Claude",
  "Format Discord Message",
  "Deliver To Discord",
];

const nodeNames = new Set(workflow.nodes.map((node) => node.name));
const missingNodes = requiredNodeNames.filter((name) => !nodeNames.has(name));

const requiredSnippets = [
  "0 17 * * 5",
  "api.github.com/repos",
  "commits?since",
  "issues?state=closed",
  "pulls?state=closed",
  "claude-sonnet-4-20250514",
  "ANTHROPIC_API_KEY",
  "GITHUB_REPO",
  "GITHUB_TOKEN",
  "DISCORD_WEBHOOK_URL",
  "SUMMARY_LANGUAGE",
  "FR",
  "EN",
];

const missingSnippets = requiredSnippets.filter((snippet) => !serialized.includes(snippet));
const setupSteps = [...readme.matchAll(/^\d+\./gm)].length;

if (missingNodes.length > 0 || missingSnippets.length > 0 || setupSteps > 5) {
  console.error(JSON.stringify({ missingNodes, missingSnippets, setupSteps }, null, 2));
  process.exit(1);
}

if (!workflow.connections["Friday 5pm Trigger"] || !workflow.connections["Build Claude Prompt"]) {
  console.error("Workflow connections are missing required execution path.");
  process.exit(1);
}

console.log(`Workflow validation passed: ${workflow.nodes.length} nodes, ${setupSteps} setup steps.`);
