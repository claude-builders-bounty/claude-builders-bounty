import fs from "node:fs";
import path from "node:path";

const root = new URL(".", import.meta.url).pathname;
const codeDir = path.join(root, "code-nodes");

function code(name) {
  return fs.readFileSync(path.join(codeDir, `${name}.js`), "utf8");
}

function node(id, name, type, typeVersion, position, parameters = {}) {
  return { parameters, id, name, type, typeVersion, position };
}

function httpHeaders(headers) {
  return {
    parameters: Object.entries(headers).map(([name, value]) => ({ name, value })),
  };
}

function connection(nodeName) {
  return { node: nodeName, type: "main", index: 0 };
}

const workflow = {
  id: "weeklyDevSummaryAviranchigoda",
  name: "Weekly GitHub Activity Summary with Claude",
  nodes: [
    node(
      "6a2f984d-8177-4d23-9458-11973555fd44",
      "Weekly Friday 5pm",
      "n8n-nodes-base.scheduleTrigger",
      1.2,
      [-820, -160],
      {
        rule: {
          interval: [
            {
              field: "cronExpression",
              expression: "0 17 * * 5",
            },
          ],
        },
      },
    ),
    node(
      "79dbd128-20a6-4547-92fe-c82cb7097e44",
      "Manual Test Trigger",
      "n8n-nodes-base.manualTrigger",
      1,
      [-820, 80],
    ),
    node(
      "56b01d5e-367f-4f8f-ac83-aac56f331243",
      "Configure Summary",
      "n8n-nodes-base.code",
      2,
      [-560, -40],
      { jsCode: code("configure-summary") },
    ),
    node(
      "8bc244f0-fd32-4264-b54d-83046979ee30",
      "Build GitHub API URLs",
      "n8n-nodes-base.code",
      2,
      [-300, -40],
      { jsCode: code("build-github-api-urls") },
    ),
    node(
      "e56e5f70-15c7-4bb6-b8d4-3761a782f2b7",
      "GitHub Commits",
      "n8n-nodes-base.httpRequest",
      4.4,
      [-20, -40],
      {
        url: "={{ $json.commitsUrl }}",
        sendHeaders: true,
        headerParameters: httpHeaders({
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "n8n-weekly-dev-summary",
        }),
        options: {
          response: {
            response: {
              responseFormat: "json",
              fullResponse: true,
            },
          },
        },
      },
    ),
    node(
      "7f7965d7-f165-4c2f-b4f4-a318f071da0b",
      "GitHub Closed Issues",
      "n8n-nodes-base.httpRequest",
      4.4,
      [260, -40],
      {
        url: '={{ $("Build GitHub API URLs").first().json.closedIssuesUrl }}',
        sendHeaders: true,
        headerParameters: httpHeaders({
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "n8n-weekly-dev-summary",
        }),
        options: {
          response: {
            response: {
              responseFormat: "json",
              fullResponse: true,
            },
          },
        },
      },
    ),
    node(
      "104a986d-3e93-471d-970f-7d67c7c88530",
      "GitHub Merged Pull Requests",
      "n8n-nodes-base.httpRequest",
      4.4,
      [540, -40],
      {
        url: '={{ $("Build GitHub API URLs").first().json.mergedPullRequestsUrl }}',
        sendHeaders: true,
        headerParameters: httpHeaders({
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "n8n-weekly-dev-summary",
        }),
        options: {
          response: {
            response: {
              responseFormat: "json",
              fullResponse: true,
            },
          },
        },
      },
    ),
    node(
      "f517054c-53a8-4fa6-8f19-52c3fdbab630",
      "Prepare Claude Request",
      "n8n-nodes-base.code",
      2,
      [820, -40],
      { jsCode: code("prepare-claude-request") },
    ),
    node(
      "ac0a88b9-bf03-4808-aec4-a59e0f33afdc",
      "Claude Summary",
      "n8n-nodes-base.httpRequest",
      4.4,
      [1100, -40],
      {
        method: "POST",
        url: "https://api.anthropic.com/v1/messages",
        sendHeaders: true,
        headerParameters: httpHeaders({
          "x-api-key": "={{ $json.anthropicApiKey }}",
          "anthropic-version": "2023-06-01",
          "content-type": "application/json",
        }),
        sendBody: true,
        specifyBody: "json",
        jsonBody: "={{ JSON.stringify($json.claudeBody) }}",
        options: {
          response: {
            response: {
              responseFormat: "json",
            },
          },
        },
      },
    ),
    node(
      "245ae83f-174c-4a73-91fc-3fc5ff95f15a",
      "Prepare Slack Message",
      "n8n-nodes-base.code",
      2,
      [1380, -40],
      { jsCode: code("prepare-slack-message") },
    ),
    node(
      "5346fe3c-cd55-4079-9619-a51a7d8ec78d",
      "Send Slack Summary",
      "n8n-nodes-base.httpRequest",
      4.4,
      [1660, -40],
      {
        method: "POST",
        url: "={{ $json.slackWebhookUrl }}",
        sendHeaders: true,
        headerParameters: httpHeaders({
          "content-type": "application/json",
        }),
        sendBody: true,
        specifyBody: "json",
        jsonBody: "={{ JSON.stringify($json.slackPayload) }}",
        options: {
          response: {
            response: {
              responseFormat: "text",
              fullResponse: true,
            },
          },
        },
      },
    ),
    node(
      "39b2f60a-30a5-4a78-b334-94e28e77f70e",
      "Execution Result",
      "n8n-nodes-base.code",
      2,
      [1940, -40],
      { jsCode: code("execution-result") },
    ),
  ],
  connections: {
    "Weekly Friday 5pm": { main: [[connection("Configure Summary")]] },
    "Manual Test Trigger": { main: [[connection("Configure Summary")]] },
    "Configure Summary": { main: [[connection("Build GitHub API URLs")]] },
    "Build GitHub API URLs": { main: [[connection("GitHub Commits")]] },
    "GitHub Commits": { main: [[connection("GitHub Closed Issues")]] },
    "GitHub Closed Issues": { main: [[connection("GitHub Merged Pull Requests")]] },
    "GitHub Merged Pull Requests": { main: [[connection("Prepare Claude Request")]] },
    "Prepare Claude Request": { main: [[connection("Claude Summary")]] },
    "Claude Summary": { main: [[connection("Prepare Slack Message")]] },
    "Prepare Slack Message": { main: [[connection("Send Slack Summary")]] },
    "Send Slack Summary": { main: [[connection("Execution Result")]] },
  },
  pinData: {},
  settings: {
    executionOrder: "v1",
  },
  staticData: null,
  tags: [],
  triggerCount: 1,
  updatedAt: "2026-05-19T00:00:00.000Z",
  versionId: "4f19ebaf-7f09-4773-a857-a29368b0b226",
};

fs.writeFileSync(path.join(root, "weekly-dev-summary.workflow.json"), `${JSON.stringify(workflow, null, 2)}\n`);
