import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const root = new URL(".", import.meta.url).pathname;
const workflowPath = path.join(root, "weekly-dev-summary.workflow.json");
const evidenceDir = path.join(root, "evidence");
const evidencePath = path.join(evidenceDir, "mock-execution-result.json");

function command(command, args, options = {}) {
  return new Promise((resolve) => {
    const child = spawn(command, args, {
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

function readBody(request) {
  return new Promise((resolve, reject) => {
    let body = "";
    request.setEncoding("utf8");
    request.on("data", (chunk) => {
      body += chunk;
    });
    request.on("end", () => resolve(body));
    request.on("error", reject);
  });
}

function startMockServer() {
  const calls = [];

  const server = http.createServer(async (request, response) => {
    const body = await readBody(request);
    calls.push({
      method: request.method,
      url: request.url,
      headers: request.headers,
      body,
    });

    if (request.method === "POST" && request.url === "/v1/messages") {
      response.writeHead(200, { "content-type": "application/json" });
      response.end(JSON.stringify({
        type: "message",
        role: "assistant",
        model: "claude-sonnet-4-20250514",
        content: [
          {
            type: "text",
            text: "Mock weekly summary: commits, issues, and merged pull requests were collected successfully.",
          },
        ],
        stop_reason: "end_turn",
        usage: {
          input_tokens: 10,
          output_tokens: 12,
        },
      }));
      return;
    }

    if (request.method === "POST" && request.url === "/slack") {
      response.writeHead(200, { "content-type": "text/plain" });
      response.end("ok");
      return;
    }

    response.writeHead(404, { "content-type": "text/plain" });
    response.end("not found");
  });

  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      resolve({
        baseUrl: `http://127.0.0.1:${address.port}`,
        calls,
        close: () => new Promise((done) => server.close(done)),
      });
    });
  });
}

function prepareWorkflowForMock(baseUrl, tempDir) {
  const workflow = JSON.parse(fs.readFileSync(workflowPath, "utf8"));
  workflow.id = "weeklyDevSummaryMock";
  workflow.name = "Weekly GitHub Activity Summary with Claude - Mock Execution";

  const configNode = workflow.nodes.find((node) => node.name === "Configure Summary");
  const claudeNode = workflow.nodes.find((node) => node.name === "Claude Summary");

  if (!configNode || !claudeNode) {
    throw new Error("Workflow is missing required Configure Summary or Claude Summary nodes.");
  }

  configNode.parameters.jsCode = configNode.parameters.jsCode
    .replace('anthropicApiKey: "REPLACE_ME_ANTHROPIC_API_KEY"', 'anthropicApiKey: "mock-anthropic-key"')
    .replace('slackWebhookUrl: "https://hooks.slack.com/services/REPLACE_ME"', `slackWebhookUrl: "${baseUrl}/slack"`);
  claudeNode.parameters.url = `${baseUrl}/v1/messages`;

  const mockWorkflowPath = path.join(tempDir, "weekly-dev-summary.mock.workflow.json");
  fs.writeFileSync(mockWorkflowPath, `${JSON.stringify(workflow, null, 2)}\n`);
  return mockWorkflowPath;
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
      // n8n prints startup log lines before raw output; keep scanning.
    }
  }

  throw new Error(`n8n raw output did not include parseable JSON: ${stdout}`);
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

const providedUserFolder = process.env.N8N_EVIDENCE_USER_FOLDER;
const tempDir = providedUserFolder || fs.mkdtempSync(path.join(os.tmpdir(), "n8n-weekly-summary-"));
const shouldRemoveTempDir = !providedUserFolder && process.env.N8N_KEEP_EVIDENCE_USER_FOLDER !== "true";
const server = await startMockServer();

try {
  const mockWorkflowPath = prepareWorkflowForMock(server.baseUrl, tempDir);
  const env = {
    ...process.env,
    N8N_USER_FOLDER: tempDir,
    N8N_SECURE_COOKIE: "false",
  };
  const n8nArgs = ["exec", "--yes", "--package", "n8n@2.20.11", "--", "n8n"];
  const importResult = await command("npm", [...n8nArgs, "import:workflow", "--input", mockWorkflowPath], { env });

  if (importResult.code !== 0 || !importResult.stdout.includes("Successfully imported 1 workflow")) {
    throw new Error(`n8n import failed\nSTDOUT:\n${importResult.stdout}\nSTDERR:\n${importResult.stderr}`);
  }

  const executeResult = await command("npm", [...n8nArgs, "execute", "--id=weeklyDevSummaryMock", "--rawOutput"], { env });

  if (executeResult.code !== 0) {
    throw new Error(`n8n execute failed\nSTDOUT:\n${executeResult.stdout}\nSTDERR:\n${executeResult.stderr}`);
  }

  const rawOutput = extractRawJson(executeResult.stdout);
  const result = extractExecutionResult(rawOutput);
  const claudeCall = server.calls.find((call) => call.url === "/v1/messages");
  const slackCall = server.calls.find((call) => call.url === "/slack");

  if (!claudeCall) {
    throw new Error(`Mock Claude endpoint was not called. Calls: ${JSON.stringify(server.calls, null, 2)}\nSTDOUT:\n${executeResult.stdout}`);
  }

  if (!slackCall) {
    throw new Error(`Mock Slack endpoint was not called. Calls: ${JSON.stringify(server.calls, null, 2)}\nSTDOUT:\n${executeResult.stdout}`);
  }

  const claudeBody = JSON.parse(claudeCall.body);
  const slackBody = JSON.parse(slackCall.body);

  if (claudeBody.model !== "claude-sonnet-4-20250514") {
    throw new Error(`Unexpected Claude model: ${claudeBody.model}`);
  }

  if (!slackBody.text?.includes("Mock weekly summary")) {
    throw new Error(`Unexpected Slack payload: ${slackCall.body}`);
  }

  if (result.status !== "delivered" || result.destination !== "slack") {
    throw new Error(`Unexpected final execution result: ${JSON.stringify(result)}`);
  }

  if (result.slackStatusCode !== 200 || result.slackResponseBody !== "ok") {
    throw new Error(`Unexpected Slack delivery response: ${JSON.stringify({
      slackStatusCode: result.slackStatusCode,
      slackResponseBody: result.slackResponseBody,
    })}`);
  }

  const evidence = {
    status: "passed",
    generatedAt: new Date().toISOString(),
    n8nPackage: "n8n@2.20.11",
    workflowId: "weeklyDevSummaryMock",
    importedWorkflow: true,
    executedWorkflow: true,
    usedRealPublicGitHubApi: true,
    claudeEndpointCalled: true,
    slackEndpointCalled: true,
    claudeRequest: {
      model: claudeBody.model,
      maxTokens: claudeBody.max_tokens,
      messageCount: claudeBody.messages?.length ?? 0,
      promptIncludesRepository: claudeBody.messages?.[0]?.content?.includes(result.repository) ?? false,
    },
    slackPayload: {
      text: slackBody.text,
      mrkdwn: slackBody.mrkdwn === true,
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
    commitCount: result.commitCount,
    closedIssueCount: result.closedIssueCount,
    mergedPullRequestCount: result.mergedPullRequestCount,
  };

  fs.mkdirSync(evidenceDir, { recursive: true });
  fs.writeFileSync(evidencePath, `${JSON.stringify(evidence, null, 2)}\n`);
  console.log(JSON.stringify(evidence, null, 2));
} finally {
  await server.close();
  if (shouldRemoveTempDir) {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}
