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
const slackWebhookPrefix = "https://hooks.slack.com/services/";

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

function evidenceContainsSecret(evidence, secrets = secretValues) {
  const renderedEvidence = JSON.stringify(evidence);
  return secrets.filter(Boolean).some((secret) => renderedEvidence.includes(secret));
}

function assertNoSecretsInEvidence(evidence, secrets = secretValues) {
  if (evidenceContainsSecret(evidence, secrets)) {
    throw new Error("Refusing to write real evidence because it contains an approval-gated secret value.");
  }
}

function runSecretGuardSelfTest() {
  const fakeSecrets = [
    "anthropic-self-test-secret",
    "slack-webhook-self-test-secret",
  ];

  assertNoSecretsInEvidence({ status: "passed", summaryLength: 42 }, fakeSecrets);

  let rejected = false;

  try {
    assertNoSecretsInEvidence({ status: "passed", leaked: fakeSecrets[0] }, fakeSecrets);
  } catch (error) {
    rejected = error.message.includes("Refusing to write real evidence");
  }

  if (!rejected) {
    throw new Error("Secret guard self-test failed to reject a synthetic secret in evidence.");
  }

  console.log(JSON.stringify({ status: "passed", check: "real evidence secret-leak guard" }, null, 2));
}

function expectValidationFailure(name, env, expectedMessage) {
  try {
    buildConfig(env);
  } catch (error) {
    if (error.message.includes(expectedMessage)) {
      return;
    }

    throw new Error(`${name} failed with unexpected message: ${error.message}`);
  }

  throw new Error(`${name} did not fail as expected.`);
}

function runInputValidationSelfTest() {
  expectValidationFailure("missing credentials", {}, "Missing required environment variable(s): ANTHROPIC_API_KEY, SLACK_WEBHOOK_URL");
  expectValidationFailure(
    "placeholder credentials",
    {
      ANTHROPIC_API_KEY: "REPLACE_ME_ANTHROPIC_API_KEY",
      SLACK_WEBHOOK_URL: "REPLACE_ME_SLACK_WEBHOOK_URL",
    },
    "Missing required environment variable(s): ANTHROPIC_API_KEY, SLACK_WEBHOOK_URL",
  );
  expectValidationFailure(
    "invalid Slack webhook",
    {
      ANTHROPIC_API_KEY: "self-test-anthropic-token",
      SLACK_WEBHOOK_URL: "https://example.invalid/webhook",
    },
    "SLACK_WEBHOOK_URL must be a Slack incoming webhook URL.",
  );
  expectValidationFailure(
    "invalid language",
    {
      ANTHROPIC_API_KEY: "self-test-anthropic-token",
      SLACK_WEBHOOK_URL: `${slackWebhookPrefix}tself/bself/self`,
      SUMMARY_LANGUAGE: "ES",
    },
    "SUMMARY_LANGUAGE must be EN or FR.",
  );
  expectValidationFailure(
    "invalid lookback",
    {
      ANTHROPIC_API_KEY: "self-test-anthropic-token",
      SLACK_WEBHOOK_URL: `${slackWebhookPrefix}tself/bself/self`,
      LOOKBACK_DAYS: "0",
    },
    "LOOKBACK_DAYS must be an integer from 1 to 31.",
  );

  const config = buildConfig({
    ANTHROPIC_API_KEY: "self-test-anthropic-token",
    SLACK_WEBHOOK_URL: `${slackWebhookPrefix}tself/bself/self`,
    GITHUB_OWNER: "example-owner",
    GITHUB_REPO: "example-repo",
    SUMMARY_LANGUAGE: "FR",
    LOOKBACK_DAYS: "14",
    SLACK_CHANNEL: "compat-channel",
  });

  if (
    config.githubOwner !== "example-owner"
    || config.githubRepo !== "example-repo"
    || config.summaryLanguage !== "FR"
    || config.lookbackDays !== 14
    || config.slackChannel !== "compat-channel"
  ) {
    throw new Error("Input validation self-test produced an unexpected valid config.");
  }

  console.log(JSON.stringify({ status: "passed", check: "real evidence input validation" }, null, 2));
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

function requireEnv(name, env = process.env) {
  const value = env[name]?.trim();

  if (!value || value.includes("REPLACE_ME")) {
    return null;
  }

  return value;
}

function optionalEnv(name, fallback, env = process.env) {
  const value = env[name]?.trim();
  return value || fallback;
}

function parseLookbackDays(env = process.env) {
  const rawValue = optionalEnv("LOOKBACK_DAYS", "7", env);
  const value = Number(rawValue);

  if (!Number.isInteger(value) || value < 1 || value > 31) {
    throw new Error("LOOKBACK_DAYS must be an integer from 1 to 31.");
  }

  return value;
}

function parseLanguage(env = process.env) {
  const value = optionalEnv("SUMMARY_LANGUAGE", "EN", env).toUpperCase();

  if (!["EN", "FR"].includes(value)) {
    throw new Error("SUMMARY_LANGUAGE must be EN or FR.");
  }

  return value;
}

function isSlackWebhookUrl(value) {
  try {
    const url = new URL(value);
    const pathParts = url.pathname.split("/").filter(Boolean);

    return url.protocol === "https:"
      && url.hostname === "hooks.slack.com"
      && pathParts[0] === "services"
      && pathParts.length >= 4;
  } catch {
    return false;
  }
}

function buildConfig(env = process.env) {
  const anthropicApiKey = requireEnv("ANTHROPIC_API_KEY", env);
  const slackWebhookUrl = requireEnv("SLACK_WEBHOOK_URL", env);
  const missing = [
    ["ANTHROPIC_API_KEY", anthropicApiKey],
    ["SLACK_WEBHOOK_URL", slackWebhookUrl],
  ].filter(([, value]) => !value).map(([name]) => name);

  if (missing.length > 0) {
    throw new Error(`Missing required environment variable(s): ${missing.join(", ")}.`);
  }

  if (!isSlackWebhookUrl(slackWebhookUrl)) {
    throw new Error("SLACK_WEBHOOK_URL must be a Slack incoming webhook URL.");
  }

  return {
    githubOwner: optionalEnv("GITHUB_OWNER", "claude-builders-bounty", env),
    githubRepo: optionalEnv("GITHUB_REPO", "claude-builders-bounty", env),
    summaryLanguage: parseLanguage(env),
    lookbackDays: parseLookbackDays(env),
    anthropicApiKey,
    slackWebhookUrl,
    slackChannel: optionalEnv("SLACK_CHANNEL", "", env),
  };
}

function safeConfigSummary(config) {
  return {
    githubOwner: config.githubOwner,
    githubRepo: config.githubRepo,
    summaryLanguage: config.summaryLanguage,
    lookbackDays: config.lookbackDays,
    hasAnthropicApiKey: true,
    hasSlackWebhookUrl: true,
    slackWebhookShape: isSlackWebhookUrl(config.slackWebhookUrl) ? "slack incoming webhook" : "invalid",
    slackChannel: config.slackChannel || "(webhook default)",
  };
}

function replaceConfigValue(jsCode, key, value) {
  const renderedValue = typeof value === "number" ? String(value) : JSON.stringify(value);
  const pattern = new RegExp(`(${key}: )[^,\\n]+`);

  if (!pattern.test(jsCode)) {
    throw new Error(`Could not find Configure Summary value for ${key}.`);
  }

  const next = jsCode.replace(pattern, (_match, prefix) => `${prefix}${renderedValue}`);

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

if (process.argv.includes("--self-test-secret-guard")) {
  runSecretGuardSelfTest();
  process.exit(0);
}

if (process.argv.includes("--self-test-input-validation")) {
  runInputValidationSelfTest();
  process.exit(0);
}

let config;

try {
  config = buildConfig();
} catch (error) {
  failClosed(error.message);
}

if (process.argv.includes("--check-env-only")) {
  console.log(JSON.stringify({
    status: "passed",
    check: "real evidence environment preflight",
    config: safeConfigSummary(config),
  }, null, 2));
  process.exit(0);
}

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

  if (typeof result.slackStatusCode !== "number" || result.slackStatusCode < 200 || result.slackStatusCode >= 300) {
    throw new Error(`Unexpected Slack status code: ${redactSecrets(result.slackStatusCode)}`);
  }

  if (result.slackResponseBody && result.slackResponseBody !== "ok" && result.slackResponseBody !== "empty") {
    throw new Error(`Unexpected Slack response body: ${redactSecrets(result.slackResponseBody)}`);
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
    slackStatusCode: result.slackStatusCode,
    slackResponseBody: result.slackResponseBody,
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

  assertNoSecretsInEvidence(evidence);
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
