import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const workflowPath = path.join(root, "weekly-dev-summary.workflow.json");
const evidenceDir = path.join(root, "evidence");
const evidencePath = path.join(evidenceDir, "real-execution-result.json");
const n8nPackage = "n8n@2.20.11";

const secretValues = [
  process.env.ANTHROPIC_API_KEY,
  process.env.SLACK_WEBHOOK_URL,
].filter(Boolean);

function redactSecrets(value) {
  let text = String(value ?? "");

  for (const secret of secretValues) {
    text = text.split(secret).join("[redacted]");
  }

  return text;
}

function command(commandName, args, options = {}) {
  return new Promise((resolve) => {
    const child = spawn(commandName, args, {
      ...options,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("close", (code) => {
      resolve({ code, stdout, stderr });
    });
  });
}

function requireEnv(name) {
  const value = process.env[name]?.trim();

  if (!value || value.includes("REPLACE_ME")) {
    return null;
  }

  return value;
}

function optionalEnv(name, fallback) {
  const value = process.env[name]?.trim();
  return value || fallback;
}

function parseLookbackDays() {
  const rawValue = optionalEnv("LOOKBACK_DAYS", "7");
  const value = Number(rawValue);

  if (!Number.isInteger(value) || value < 1 || value > 31) {
    throw new Error("LOOKBACK_DAYS must be an integer from 1 to 31.");
  }

  return value;
}

function parseLanguage() {
  const value = optionalEnv("SUMMARY_LANGUAGE", "EN").toUpperCase();

  if (!["EN", "FR"].includes(value)) {
    throw new Error("SUMMARY_LANGUAGE must be EN or FR.");
  }

  return value;
}

function replaceConfigValue(jsCode, key, value) {
  const renderedValue = typeof value === "number" ? String(value) : JSON.stringify(value);
  const pattern = new RegExp(`(${key}: )[^,\\n]+`);
  const next = jsCode.replace(pattern, (_match, prefix) => `${prefix}${renderedValue}`);

  if (next === jsCode) {
    throw new Error(`Could not update Configure Summary value for ${key}.`);
  }

  return next;
}

function prepareWorkflowForReal(config, tempDir) {
  const workflow = JSON.parse(fs.readFileSync(workflowPath, "utf8"));
  workflow.id = "weeklyDevSummaryRealEvidence";
  workflow.name = "Weekly GitHub Activity Summary with Claude - Real Evidence";

  const configNode = workflow.nodes.find((node) => node.name === "Configure Summary");

  if (!configNode) {
    throw new Error("Workflow is missing required Configure Summary node.");
  }

  let jsCode = configNode.parameters.jsCode;
  jsCode = replaceConfigValue(jsCode, "githubOwner", config.githubOwner);
  jsCode = replaceConfigValue(jsCode, "githubRepo", config.githubRepo);
  jsCode = replaceConfigValue(jsCode, "summaryLanguage", config.summaryLanguage);
  jsCode = replaceConfigValue(jsCode, "lookbackDays", config.lookbackDays);
  jsCode = replaceConfigValue(jsCode, "anthropicApiKey", config.anthropicApiKey);
  jsCode = replaceConfigValue(jsCode, "slackWebhookUrl", config.slackWebhookUrl);
  jsCode = replaceConfigValue(jsCode, "slackChannel", config.slackChannel);
  configNode.parameters.jsCode = jsCode;

  const realWorkflowPath = path.join(tempDir, "weekly-dev-summary.real.workflow.json");
  fs.writeFileSync(realWorkflowPath, `${JSON.stringify(workflow, null, 2)}\n`);
  return realWorkflowPath;
}

function extractRawJson(stdout) {
  const trimmed = stdout.trim();
  const starts = [];

  for (let index = 0; index < trimmed.length; index += 1) {
    if (trimmed[index] === "[" || trimmed[index] === "{") {
      starts.push(index);
    }
  }

  for (const start of starts.reverse()) {
    try {
      return JSON.parse(trimmed.slice(start));
    } catch {
      // n8n can print startup log lines before raw output; keep scanning.
    }
  }

  throw new Error(`n8n raw output did not include parseable JSON: ${redactSecrets(stdout)}`);
}

function extractExecutionResult(rawOutput) {
  if (Array.isArray(rawOutput)) {
    return rawOutput[0]?.json;
  }

  const executionResult = rawOutput?.data?.resultData?.runData?.["Execution Result"]?.[0]?.data?.main?.[0]?.[0]?.json;

  if (executionResult) {
    return executionResult;
  }

  return rawOutput?.json ?? rawOutput;
}

function failClosed(message) {
  console.error(message);
  console.error("Refusing to run a real n8n execution until approval-gated credentials are supplied as environment variables.");
  process.exit(1);
}

const anthropicApiKey = requireEnv("ANTHROPIC_API_KEY");
const slackWebhookUrl = requireEnv("SLACK_WEBHOOK_URL");
const missing = [
  ["ANTHROPIC_API_KEY", anthropicApiKey],
  ["SLACK_WEBHOOK_URL", slackWebhookUrl],
].filter(([, value]) => !value).map(([name]) => name);

if (missing.length > 0) {
  failClosed(`Missing required environment variable(s): ${missing.join(", ")}.`);
}

if (!slackWebhookUrl.startsWith("https://hooks.slack.com/services/")) {
  failClosed("SLACK_WEBHOOK_URL must be a Slack incoming webhook URL.");
}

const config = {
  githubOwner: optionalEnv("GITHUB_OWNER", "claude-builders-bounty"),
  githubRepo: optionalEnv("GITHUB_REPO", "claude-builders-bounty"),
  summaryLanguage: parseLanguage(),
  lookbackDays: parseLookbackDays(),
  anthropicApiKey,
  slackWebhookUrl,
  slackChannel: optionalEnv("SLACK_CHANNEL", ""),
};

const providedUserFolder = process.env.N8N_REAL_EVIDENCE_USER_FOLDER;
const n8nUserFolder = providedUserFolder || fs.mkdtempSync(path.join(os.tmpdir(), "n8n-weekly-summary-real-user-"));
const workflowTempDir = fs.mkdtempSync(path.join(os.tmpdir(), "n8n-weekly-summary-real-import-"));
const shouldRemoveUserFolder = !providedUserFolder && process.env.N8N_KEEP_REAL_EVIDENCE_USER_FOLDER !== "true";
fs.mkdirSync(n8nUserFolder, { recursive: true });

try {
  const realWorkflowPath = prepareWorkflowForReal(config, workflowTempDir);
  const env = {
    ...process.env,
    N8N_USER_FOLDER: n8nUserFolder,
    N8N_SECURE_COOKIE: "false",
  };
  const n8nArgs = ["exec", "--yes", "--package", n8nPackage, "--", "n8n"];
  const importResult = await command("npm", [...n8nArgs, "import:workflow", "--input", realWorkflowPath], { env });

  if (importResult.code !== 0 || !importResult.stdout.includes("Successfully imported 1 workflow")) {
    throw new Error(`n8n import failed\nSTDOUT:\n${redactSecrets(importResult.stdout)}\nSTDERR:\n${redactSecrets(importResult.stderr)}`);
  }

  const executeResult = await command("npm", [...n8nArgs, "execute", "--id=weeklyDevSummaryRealEvidence", "--rawOutput"], { env });

  if (executeResult.code !== 0) {
    throw new Error(`n8n execute failed\nSTDOUT:\n${redactSecrets(executeResult.stdout)}\nSTDERR:\n${redactSecrets(executeResult.stderr)}`);
  }

  const rawOutput = extractRawJson(executeResult.stdout);
  const result = extractExecutionResult(rawOutput);

  if (result.status !== "delivered" || result.destination !== "slack") {
    throw new Error(`Unexpected final execution result: ${redactSecrets(JSON.stringify(result))}`);
  }

  const evidence = {
    status: "passed",
    generatedAt: new Date().toISOString(),
    n8nPackage,
    workflowId: "weeklyDevSummaryRealEvidence",
    importedWorkflow: true,
    executedWorkflow: true,
    usedRealPublicGitHubApi: true,
    usedRealAnthropicApi: true,
    usedRealSlackWebhook: true,
    claudeRequest: {
      model: "claude-sonnet-4-20250514",
      maxTokens: 1200,
    },
    n8nExecution: {
      status: rawOutput?.status ?? rawOutput?.data?.status,
      finished: rawOutput?.finished === true || rawOutput?.data?.finished === true,
      lastNodeExecuted: rawOutput?.data?.resultData?.lastNodeExecuted,
    },
    finalStatus: result.status,
    destination: result.destination,
    repository: result.repository,
    periodStart: result.periodStart,
    periodEnd: result.periodEnd,
    language: result.language,
    commitCount: result.commitCount,
    closedIssueCount: result.closedIssueCount,
    mergedPullRequestCount: result.mergedPullRequestCount,
    slackChannel: result.slackChannel,
    summaryLength: typeof result.summary === "string" ? result.summary.length : 0,
  };

  fs.mkdirSync(evidenceDir, { recursive: true });
  fs.writeFileSync(evidencePath, `${JSON.stringify(evidence, null, 2)}\n`);
  console.log(JSON.stringify(evidence, null, 2));
} catch (error) {
  console.error(redactSecrets(error.stack || error.message || error));
  process.exitCode = 1;
} finally {
  fs.rmSync(workflowTempDir, { recursive: true, force: true });
  if (shouldRemoveUserFolder) {
    fs.rmSync(n8nUserFolder, { recursive: true, force: true });
  }
}
