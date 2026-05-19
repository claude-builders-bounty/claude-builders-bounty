import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const workflowPath = path.join(root, "weekly-dev-summary.workflow.json");
const readmePath = path.join(root, "README.md");
const acceptanceMatrixPath = path.join(root, "ACCEPTANCE_MATRIX.md");
const evidenceDir = path.join(root, "evidence");
const resultPath = path.join(evidenceDir, "acceptance-check-result.json");
const requireRealEvidence = process.argv.includes("--require-real-evidence");
const writeResult = !process.argv.includes("--no-write");

const checks = [];
const failures = [];
const approvalGates = [];

function readText(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

function check(name, passed, evidence) {
  const entry = { name, passed: Boolean(passed), evidence };
  checks.push(entry);

  if (!entry.passed) {
    failures.push({ name, evidence });
  }
}

function gate(name, passed, nextAction) {
  const entry = { name, passed: Boolean(passed), nextAction };

  if (!entry.passed && requireRealEvidence) {
    failures.push({ name, evidence: nextAction });
  } else if (!entry.passed) {
    approvalGates.push(entry);
  }

  return entry;
}

function node(workflow, name) {
  return workflow.nodes.find((candidate) => candidate.name === name);
}

function headerValue(httpNode, headerName) {
  return httpNode?.parameters?.headerParameters?.parameters
    ?.find((header) => header.name.toLowerCase() === headerName.toLowerCase())
    ?.value;
}

function responseOption(httpNode, key) {
  return httpNode?.parameters?.options?.response?.response?.[key];
}

function countSetupSteps(readme) {
  const lines = readme.split("\n");
  const setupIndex = lines.findIndex((line) => line.trim() === "## Setup");

  if (setupIndex === -1) {
    return null;
  }

  let count = 0;

  for (let index = setupIndex + 1; index < lines.length; index += 1) {
    const line = lines[index];

    if (line.startsWith("## ")) {
      break;
    }

    if (/^\d+\.\s/.test(line)) {
      count += 1;
    }
  }

  return count;
}

function walkFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(directory, entry.name);

    if (entry.isDirectory()) {
      return walkFiles(fullPath);
    }

    return fullPath;
  });
}

function pngInfo(filePath) {
  if (!fs.existsSync(filePath)) {
    return { exists: false, valid: false, evidence: "missing file" };
  }

  const buffer = fs.readFileSync(filePath);
  const signature = buffer.subarray(0, 8);
  const pngSignature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const validSignature = signature.equals(pngSignature);
  const width = buffer.length >= 24 ? buffer.readUInt32BE(16) : 0;
  const height = buffer.length >= 24 ? buffer.readUInt32BE(20) : 0;
  const valid = validSignature && width >= 800 && height >= 500;

  return {
    exists: true,
    valid,
    width,
    height,
    sizeBytes: buffer.length,
    evidence: valid
      ? `valid PNG ${width}x${height}, ${buffer.length} bytes`
      : `invalid or too small PNG ${width}x${height}, ${buffer.length} bytes`,
  };
}

function realEvidenceInfo(filePath) {
  if (!fs.existsSync(filePath)) {
    return { valid: false, evidence: "missing file" };
  }

  let evidence;

  try {
    evidence = JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    return { valid: false, evidence: `invalid JSON: ${error.message}` };
  }

  const requiredFields = {
    status: "passed",
    importedWorkflow: true,
    executedWorkflow: true,
    usedRealPublicGitHubApi: true,
    usedRealAnthropicApi: true,
    usedRealSlackWebhook: true,
    finalStatus: "delivered",
    destination: "slack",
  };
  const mismatches = Object.entries(requiredFields)
    .filter(([key, expected]) => evidence[key] !== expected)
    .map(([key, expected]) => `${key} expected ${JSON.stringify(expected)} got ${JSON.stringify(evidence[key])}`);

  if (evidence.claudeRequest?.model !== "claude-sonnet-4-20250514") {
    mismatches.push(`claudeRequest.model expected "claude-sonnet-4-20250514" got ${JSON.stringify(evidence.claudeRequest?.model)}`);
  }

  if (typeof evidence.summaryLength !== "number" || evidence.summaryLength <= 0) {
    mismatches.push(`summaryLength expected positive number got ${JSON.stringify(evidence.summaryLength)}`);
  }

  if (typeof evidence.slackStatusCode !== "number" || evidence.slackStatusCode < 200 || evidence.slackStatusCode >= 300) {
    mismatches.push(`slackStatusCode expected 2xx number got ${JSON.stringify(evidence.slackStatusCode)}`);
  }

  if (typeof evidence.slackResponseBody === "string" && evidence.slackResponseBody && evidence.slackResponseBody !== "ok" && evidence.slackResponseBody !== "empty") {
    mismatches.push(`slackResponseBody expected "ok" or "empty" got ${JSON.stringify(evidence.slackResponseBody)}`);
  }

  if (mismatches.length > 0) {
    return { valid: false, evidence: mismatches.join("; ") };
  }

  return {
    valid: true,
    evidence: "real execution evidence reports delivered Slack summary from real GitHub, Anthropic, and Slack endpoints",
  };
}

const workflow = JSON.parse(fs.readFileSync(workflowPath, "utf8"));
const readme = fs.readFileSync(readmePath, "utf8");
const acceptanceMatrix = fs.existsSync(acceptanceMatrixPath)
  ? fs.readFileSync(acceptanceMatrixPath, "utf8")
  : "";
const configCode = readText("code-nodes/configure-summary.js");
const buildUrlsCode = readText("code-nodes/build-github-api-urls.js");
const prepareClaudeCode = readText("code-nodes/prepare-claude-request.js");
const prepareSlackCode = readText("code-nodes/prepare-slack-message.js");
const executionResultCode = readText("code-nodes/execution-result.js");
const mockRunnerCode = readText("validate-mock-execution.mjs");
const realRunnerCode = readText("validate-real-execution.mjs");

check(
  "exportable n8n workflow JSON",
  workflow.id && workflow.name && Array.isArray(workflow.nodes) && workflow.connections,
  `workflow ${workflow.id || "(missing id)"} has ${workflow.nodes?.length ?? 0} nodes`,
);

const schedule = node(workflow, "Weekly Friday 5pm");
check(
  "weekly Friday 5pm schedule trigger",
  schedule?.type === "n8n-nodes-base.scheduleTrigger"
    && schedule.parameters?.rule?.interval?.[0]?.expression === "0 17 * * 5",
  schedule?.parameters?.rule?.interval?.[0]?.expression ?? "missing schedule expression",
);

check(
  "manual test trigger",
  node(workflow, "Manual Test Trigger")?.type === "n8n-nodes-base.manualTrigger",
  "Manual Test Trigger node exists for reviewer execution",
);

const githubNodes = ["GitHub Commits", "GitHub Closed Issues", "GitHub Merged Pull Requests"].map((name) => node(workflow, name));
check(
  "GitHub HTTP Request nodes",
  githubNodes.every((githubNode) => githubNode?.type === "n8n-nodes-base.httpRequest"),
  githubNodes.map((githubNode) => githubNode?.name ?? "missing").join(", "),
);

check(
  "GitHub activity coverage",
  buildUrlsCode.includes("/commits")
    && buildUrlsCode.includes("type:issue is:closed")
    && buildUrlsCode.includes("type:pr is:merged"),
  "Build GitHub API URLs covers commits, closed issues, and merged PRs",
);

check(
  "GitHub empty-array preservation",
  githubNodes.every((githubNode) => responseOption(githubNode, "fullResponse") === true),
  "GitHub HTTP nodes use fullResponse so quiet weeks continue downstream",
);

const claudeNode = node(workflow, "Claude Summary");
check(
  "Claude HTTP Request node",
  claudeNode?.type === "n8n-nodes-base.httpRequest"
    && claudeNode.parameters?.method === "POST"
    && claudeNode.parameters?.url === "https://api.anthropic.com/v1/messages",
  claudeNode?.parameters?.url ?? "missing Claude URL",
);

check(
  "Claude model",
  prepareClaudeCode.includes('model: "claude-sonnet-4-20250514"'),
  "Prepare Claude Request uses claude-sonnet-4-20250514",
);

check(
  "Claude API headers",
  headerValue(claudeNode, "x-api-key") === "={{ $json.anthropicApiKey }}"
    && headerValue(claudeNode, "anthropic-version") === "2023-06-01",
  "Claude request reads API key from workflow config and sets anthropic-version",
);

const slackNode = node(workflow, "Send Slack Summary");
check(
  "Slack webhook delivery",
  slackNode?.type === "n8n-nodes-base.httpRequest"
    && slackNode.parameters?.method === "POST"
    && slackNode.parameters?.url === "={{ $json.slackWebhookUrl }}"
    && prepareSlackCode.includes("slackPayload")
    && prepareSlackCode.includes("mrkdwn: true"),
  slackNode?.parameters?.url ?? "missing Slack URL",
);

check(
  "Slack response validation",
  executionResultCode.includes('"Send Slack Summary"')
    && executionResultCode.includes("slackStatusCode")
    && executionResultCode.includes("Slack webhook returned unexpected status code")
    && executionResultCode.includes("Slack webhook returned unexpected body"),
  "Execution Result verifies the Slack HTTP response before reporting delivered",
);

check(
  "configurable repo, destination, and language",
  ["githubOwner", "githubRepo", "summaryLanguage", "slackWebhookUrl", "slackChannel"].every((key) => configCode.includes(key))
    && configCode.includes('["EN", "FR"]'),
  "Configure Summary exposes GitHub repo, Slack destination, and EN/FR language",
);

check(
  "README setup instructions in five steps or fewer",
  countSetupSteps(readme) !== null && countSetupSteps(readme) <= 5,
  `${countSetupSteps(readme) ?? 0} setup steps found`,
);

check(
  "reviewer acceptance matrix",
  [
    "Weekly Friday 5pm",
    "GitHub Commits",
    "GitHub Closed Issues",
    "GitHub Merged Pull Requests",
    "claude-sonnet-4-20250514",
    "Slack delivery",
    "mock Slack failure",
    "Real Anthropic and Slack execution evidence",
    "No committed secrets",
  ].every((needle) => acceptanceMatrix.includes(needle)),
  acceptanceMatrix
    ? "ACCEPTANCE_MATRIX.md maps issue requirements to artifacts, local evidence, and approval gates"
    : "missing ACCEPTANCE_MATRIX.md",
);

const codeNodeSources = new Map([
  ["Configure Summary", "configure-summary.js"],
  ["Build GitHub API URLs", "build-github-api-urls.js"],
  ["Prepare Claude Request", "prepare-claude-request.js"],
  ["Prepare Slack Message", "prepare-slack-message.js"],
  ["Execution Result", "execution-result.js"],
]);

for (const [nodeName, fileName] of codeNodeSources) {
  check(
    `embedded Code node matches ${fileName}`,
    node(workflow, nodeName)?.parameters?.jsCode === readText(path.join("code-nodes", fileName)),
    `${nodeName} is synchronized with code-nodes/${fileName}`,
  );
}

const mockEvidencePath = path.join(evidenceDir, "mock-execution-result.json");
const mockSlackFailureEvidencePath = path.join(evidenceDir, "mock-slack-failure-result.json");
const mockScreenshotPath = path.join(evidenceDir, "mock-n8n-execution-ui.png");
const mockScreenshot = pngInfo(mockScreenshotPath);
const mockSlackFailureEvidence = fs.existsSync(mockSlackFailureEvidencePath)
  ? JSON.parse(fs.readFileSync(mockSlackFailureEvidencePath, "utf8"))
  : null;
check(
  "local mock n8n execution evidence",
  fs.existsSync(mockEvidencePath) && JSON.parse(fs.readFileSync(mockEvidencePath, "utf8")).finalStatus === "delivered",
  "mock execution evidence exists and reports delivered",
);
check(
  "local mock Slack failure rejection evidence",
  mockSlackFailureEvidence?.status === "passed"
    && mockSlackFailureEvidence.expectedSlackFailure === true
    && mockSlackFailureEvidence.slackEndpointCalled === true
    && mockSlackFailureEvidence.deliveredResultRejected === true,
  mockSlackFailureEvidence
    ? `Slack failure rejected with n8n exit code ${mockSlackFailureEvidence.n8nExitCode}`
    : "missing mock Slack failure evidence",
);
check(
  "local mock validator no-write mode",
  mockRunnerCode.includes("--no-write")
    && mockRunnerCode.includes("writeEvidence")
    && mockRunnerCode.includes("writeAndPrintEvidence")
    && mockRunnerCode.includes("N8N_RUNNERS_BROKER_PORT"),
  "validate-mock-execution.mjs can rerun mock success and failure validation without rewriting evidence files or colliding on n8n's task-broker port",
);
check(
  "local mock n8n UI screenshot",
  mockScreenshot.valid,
  mockScreenshot.evidence,
);

check(
  "real evidence secret-leak guard",
  realRunnerCode.includes("assertNoSecretsInEvidence")
    && realRunnerCode.includes("evidenceContainsSecret")
    && realRunnerCode.includes("--self-test-secret-guard")
    && realRunnerCode.includes("Refusing to write real evidence")
    && realRunnerCode.includes("secrets.filter(Boolean).some"),
  "validate-real-execution.mjs refuses to write sanitized evidence if an approval-gated secret appears in it and exposes a local self-test for the guard",
);

check(
  "real evidence environment preflight",
  realRunnerCode.includes("--check-env-only")
    && realRunnerCode.includes("--self-test-input-validation")
    && realRunnerCode.includes("buildConfig")
    && realRunnerCode.includes("isSlackWebhookUrl")
    && realRunnerCode.includes("safeConfigSummary")
    && realRunnerCode.includes("real evidence environment preflight"),
  "validate-real-execution.mjs can validate approval-gated environment variables without network calls or evidence writes",
);

const realEvidencePath = path.join(evidenceDir, "real-execution-result.json");
const realScreenshotPath = path.join(evidenceDir, "real-n8n-execution-ui.png");
const realEvidence = realEvidenceInfo(realEvidencePath);
const realScreenshot = pngInfo(realScreenshotPath);
const realEvidenceGate = gate(
  "real Anthropic and Slack execution evidence",
  realEvidence.valid,
  `Run validate-real-execution.mjs with ANTHROPIC_API_KEY and SLACK_WEBHOOK_URL after user approval; see REAL_EVIDENCE.md. Current state: ${realEvidence.evidence}.`,
);
const realScreenshotGate = gate(
  "real n8n execution screenshot",
  realScreenshot.valid,
  `Capture evidence/real-n8n-execution-ui.png from the real n8n execution after credentials are supplied; current state: ${realScreenshot.evidence}.`,
);

const secretPattern = new RegExp([
  "sk-" + "ant-",
  "xox" + "[baprs]-",
  "gh" + "p_",
  "github" + "_pat_",
  "hooks\\.slack\\.com\\/services\\/[A-Z0-9]+\\/[A-Z0-9]+\\/[A-Za-z0-9]+",
].join("|"));
const filesWithSecrets = walkFiles(root)
  .filter((filePath) => !filePath.includes(`${path.sep}.git${path.sep}`))
  .filter((filePath) => secretPattern.test(fs.readFileSync(filePath, "utf8")));

check(
  "no committed API keys or real webhook tokens",
  filesWithSecrets.length === 0,
  filesWithSecrets.map((filePath) => path.relative(root, filePath)).join(", ") || "no matching secret patterns",
);

const result = {
  status: failures.length === 0 ? "passed" : "failed",
  generatedAt: new Date().toISOString(),
  requireRealEvidence,
  checks,
  approvalGates: [realEvidenceGate, realScreenshotGate].filter((entry) => !entry.passed),
  failures,
};

if (writeResult) {
  fs.mkdirSync(evidenceDir, { recursive: true });
  fs.writeFileSync(resultPath, `${JSON.stringify(result, null, 2)}\n`);
}
console.log(JSON.stringify(result, null, 2));

if (failures.length > 0) {
  process.exit(1);
}
