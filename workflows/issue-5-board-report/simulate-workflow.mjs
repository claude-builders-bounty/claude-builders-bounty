import fs from "node:fs";
import http from "node:http";
import vm from "node:vm";
import { setTimeout as delay } from "node:timers/promises";

const workflowPath = new URL("./weekly-board-report.workflow.json", import.meta.url);
const workflow = JSON.parse(fs.readFileSync(workflowPath, "utf8"));
const codeByName = Object.fromEntries(
  workflow.nodes
    .filter((node) => node.type === "n8n-nodes-base.code")
    .map((node) => [node.name, node.parameters.jsCode])
);

const received = [];
const server = http.createServer((req, res) => {
  const url = new URL(req.url || "/", `http://${req.headers.host}`);
  const send = (body, status = 200) => {
    res.writeHead(status, { "content-type": "application/json" });
    res.end(JSON.stringify(body));
  };

  if (req.method === "GET" && url.pathname.includes("/commits")) {
    send([
      {
        sha: "6a1f0d4b8c9e",
        commit: { author: { name: "Maya", date: "2026-06-01T10:00:00Z" }, message: "Add weekly digest renderer" },
        author: { login: "maya-dev" },
        html_url: "https://github.example/repo/commit/6a1f0d4"
      },
      {
        sha: "81bd20aac917",
        commit: { author: { name: "Ari", date: "2026-06-02T12:00:00Z" }, message: "Hotfix report timezone handling" },
        author: { login: "ari-ops" },
        html_url: "https://github.example/repo/commit/81bd20a"
      }
    ]);
    return;
  }

  if (req.method === "GET" && url.pathname === "/search/issues") {
    const query = url.searchParams.get("q") || "";
    send({
      items: query.includes("is:pr")
        ? [
            {
              number: 77,
              title: "Ship board-style weekly report",
              closed_at: "2026-06-02T18:30:00Z",
              user: { login: "maya-dev" },
              html_url: "https://github.example/repo/pull/77"
            }
          ]
        : [
            {
              number: 42,
              title: "Weekly email summary skips empty weeks",
              labels: [{ name: "bug" }],
              closed_at: "2026-06-02T16:20:00Z",
              user: { login: "pm-user" },
              html_url: "https://github.example/repo/issues/42"
            }
          ]
    });
    return;
  }

  if (req.method === "POST" && url.pathname === "/v1/messages") {
    send({
      id: "msg_mock_success",
      type: "message",
      role: "assistant",
      model: "claude-sonnet-4-20250514",
      content: [
        {
          type: "text",
          text: [
            "## Executive Pulse",
            "- The repository had steady delivery activity with 2 commits and 1 merged PR.",
            "- One customer-facing issue was closed.",
            "- One hotfix signal should be reviewed after the weekly report.",
            "",
            "## Narrative Summary",
            "The team shipped a board-style weekly report flow and closed the empty-week summary issue while tightening timezone handling.",
            "",
            "## What Shipped",
            "- PR #77 shipped the board-style weekly report.",
            "",
            "## Issues Closed",
            "- Issue #42 resolved skipped summaries for empty weeks.",
            "",
            "## Contributor Spotlight",
            "Maya and Ari both contributed meaningful delivery work this week.",
            "",
            "## Risk Radar",
            "Observed one hotfix signal in commit 81bd20a; review timezone behavior after deployment.",
            "",
            "## Audit Trail",
            "2 commits, 1 merged PR, 1 closed issue."
          ].join("\n")
        }
      ]
    });
    return;
  }

  if (req.method === "POST" && url.pathname === "/discord") {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", () => {
      received.push(JSON.parse(body || "{}"));
      send({ ok: true, received: received.length });
    });
    return;
  }

  send({ error: "not found", path: url.pathname }, 404);
});

function listen() {
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve(server.address().port));
  });
}

async function runCode(name, json, extra = {}) {
  const context = {
    $json: json,
    $env: extra.env,
    fetch,
    helpers: {
      httpRequest: async ({ url, method = "GET", headers = {}, body, json: wantsJson }) => {
        const response = await fetch(url, {
          method,
          headers,
          body: body ? JSON.stringify(body) : undefined
        });
        if (!response.ok) {
          throw new Error(`HTTP ${method} ${url} failed with ${response.status}`);
        }
        return wantsJson ? response.json() : response.text();
      }
    },
    console,
    ...extra.globals
  };
  const script = new vm.Script(`(async () => {\n${codeByName[name]}\n})()`, { filename: `${name}.js` });
  return script.runInNewContext(context);
}

const port = await listen();
const base = `http://127.0.0.1:${port}`;

try {
  const env = {
    GITHUB_REPO: "example/board-report",
    GITHUB_TOKEN: "ghp_mock",
    ANTHROPIC_API_KEY: "sk-ant-mock",
    DISCORD_WEBHOOK_URL: `${base}/discord`,
    GITHUB_API_BASE_URL: base,
    ANTHROPIC_API_BASE_URL: base,
    SUMMARY_LANGUAGE: "EN"
  };

  const config = (await runCode("Load Config and Date Window", {}, { env }))[0].json;
  const activity = (await runCode("Collect GitHub Activity", config, { env }))[0].json;
  const request = (await runCode("Build Claude Board Brief", activity, { env }))[0].json;

  const claudeResponse = await fetch(request.anthropicMessagesUrl, {
    method: "POST",
    headers: {
      "x-api-key": request.anthropicApiKey,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json"
    },
    body: JSON.stringify(request.claudeRequest)
  }).then((res) => res.json());

  const prepared = (await runCode("Prepare Discord Delivery", claudeResponse, {
    env,
    globals: {
      $: (nodeName) => ({
        first: () => {
          if (nodeName === "Build Claude Board Brief") return { json: request };
          throw new Error(`Unexpected node lookup: ${nodeName}`);
        }
      })
    }
  }))[0].json;

  await fetch(prepared.discordWebhookUrl, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(prepared.discordPayload)
  });

  await delay(20);

  console.log(JSON.stringify({
    ok: true,
    stats: activity.stats,
    claudeModel: request.claudeRequest.model,
    discordMessages: received.length,
    discordTitle: received[0]?.embeds?.[0]?.title,
    summaryHasRiskRadar: prepared.summary.includes("Risk Radar")
  }, null, 2));
} finally {
  server.close();
}
