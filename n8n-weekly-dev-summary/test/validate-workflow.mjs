#!/usr/bin/env node
/**
 * Structural validation for weekly-dev-summary.json.
 *
 * Checks what n8n silently tolerates on import but breaks on at run time:
 * unique node ids and names, connections that point at existing nodes,
 * required fields per node type, cron validity, and JS syntax in every Code node.
 *
 *   node test/validate-workflow.mjs
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const workflowPath = join(here, "..", "weekly-dev-summary.json");
const workflow = JSON.parse(readFileSync(workflowPath, "utf8"));

const problems = [];
const warnings = [];
const fail = (message) => problems.push(message);

// --- top level ---------------------------------------------------------------
if (!workflow.name) fail("workflow has no name");
if (!Array.isArray(workflow.nodes) || workflow.nodes.length === 0) fail("workflow has no nodes");
if (typeof workflow.connections !== "object") fail("workflow has no connections object");
if (workflow.active !== false) fail("workflow must be imported inactive (active: false)");

const nodes = workflow.nodes ?? [];
const names = new Set();
const ids = new Set();

for (const node of nodes) {
  if (!node.name) fail(`node without name: ${JSON.stringify(node).slice(0, 80)}`);
  if (names.has(node.name)) fail(`duplicate node name: ${node.name}`);
  names.add(node.name);
  if (!node.id) fail(`node ${node.name} has no id`);
  if (ids.has(node.id)) fail(`duplicate node id: ${node.id}`);
  ids.add(node.id);
  if (!node.type?.startsWith("n8n-nodes-base.")) fail(`node ${node.name} has an unexpected type: ${node.type}`);
  if (typeof node.typeVersion !== "number") fail(`node ${node.name} has no typeVersion`);
  if (!Array.isArray(node.position) || node.position.length !== 2) fail(`node ${node.name} has no position`);
  if (!node.parameters || typeof node.parameters !== "object") fail(`node ${node.name} has no parameters`);
}

// --- connections -------------------------------------------------------------
for (const [source, groups] of Object.entries(workflow.connections ?? {})) {
  if (!names.has(source)) fail(`connection from unknown node: ${source}`);
  for (const outputs of groups.main ?? []) {
    for (const connection of outputs ?? []) {
      if (!names.has(connection.node)) fail(`connection to unknown node: ${connection.node} (from ${source})`);
      if (connection.type !== "main") fail(`connection type must be main (from ${source})`);
    }
  }
}

// --- reachability ------------------------------------------------------------
const reached = new Set();
const stack = ["Every Friday 17:00", "Manual Test"];
while (stack.length) {
  const current = stack.pop();
  if (reached.has(current)) continue;
  reached.add(current);
  for (const outputs of workflow.connections[current]?.main ?? []) {
    for (const connection of outputs ?? []) stack.push(connection.node);
  }
}
for (const node of nodes) {
  if (!reached.has(node.name)) warnings.push(`node not reachable from a trigger: ${node.name}`);
}

// --- per type ----------------------------------------------------------------
const byName = Object.fromEntries(nodes.map((node) => [node.name, node]));

const schedule = nodes.find((node) => node.type === "n8n-nodes-base.scheduleTrigger");
const cron = schedule?.parameters?.rule?.interval?.[0]?.expression;
if (!cron) fail("schedule trigger has no cron expression");
else if (cron.trim().split(/\s+/).length !== 5) fail(`cron must have 5 fields: "${cron}"`);

const config = byName["Config"];
if (!config) fail("Config node is missing");
else {
  const assignments = config.parameters?.assignments?.assignments ?? [];
  const assigned = new Set(assignments.map((a) => a.name));
  for (const required of [
    "owner",
    "repo",
    "language",
    "model",
    "anthropicBaseUrl",
    "anthropicApiKey",
    "githubToken",
    "discordWebhookUrl",
  ]) {
    if (!assigned.has(required)) fail(`Config is missing the "${required}" variable`);
  }
  const model = assignments.find((a) => a.name === "model")?.value;
  if (model !== "claude-sonnet-4-20250514") fail(`Config.model must default to claude-sonnet-4-20250514, got ${model}`);
  const language = assignments.find((a) => a.name === "language")?.value;
  if (!["en", "fr"].includes(language)) fail(`Config.language must be en or fr, got ${language}`);
}

const httpNodes = nodes.filter((node) => node.type === "n8n-nodes-base.httpRequest");
const claude = httpNodes.find((node) => node.name === "Claude: Weekly Summary");
if (!claude) fail("Claude request node is missing");
else {
  const body = claude.parameters?.jsonBody ?? "";
  if (!body.includes("messages")) fail("Claude node body has no messages array");
  const headers = (claude.parameters?.headerParameters?.parameters ?? []).map((h) => h.name);
  for (const header of ["x-api-key", "anthropic-version"]) {
    if (!headers.includes(header)) fail(`Claude node is missing the ${header} header`);
  }
}

const discord = httpNodes.find((node) => node.name === "Discord: Post Summary");
if (!discord) fail("Discord delivery node is missing");

// --- JavaScript inside Code nodes --------------------------------------------
for (const node of nodes.filter((n) => n.type === "n8n-nodes-base.code")) {
  const code = node.parameters?.jsCode;
  if (!code) {
    fail(`Code node ${node.name} has no jsCode`);
    continue;
  }
  try {
    // Parse only. n8n globals ($json, $(), $input) are provided at run time.
    new Function("$json", "$", "$input", "$now", code);
  } catch (error) {
    fail(`Code node ${node.name} has a syntax error: ${error.message}`);
  }
}

for (const problem of problems) console.error(`FAIL ${problem}`);
for (const warning of warnings) console.warn(`WARN ${warning}`);
console.log(`\n${nodes.length} nodes, ${Object.keys(workflow.connections ?? {}).length} connection groups, ${problems.length} problems, ${warnings.length} warnings`);
process.exit(problems.length ? 1 : 0);
