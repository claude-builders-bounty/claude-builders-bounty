import http from "node:http";

const port = Number(process.env.PORT || 8787);
const received = [];

function json(res, body, status = 200) {
  res.writeHead(status, { "content-type": "application/json" });
  res.end(JSON.stringify(body));
}

const commits = [
  {
    sha: "6a1f0d4b8c9e",
    commit: {
      author: { name: "Maya", date: "2026-06-01T10:00:00Z" },
      message: "Add weekly digest renderer"
    },
    author: { login: "maya-dev" },
    html_url: "https://github.example/repo/commit/6a1f0d4"
  },
  {
    sha: "81bd20aac917",
    commit: {
      author: { name: "Ari", date: "2026-06-02T12:00:00Z" },
      message: "Hotfix report timezone handling"
    },
    author: { login: "ari-ops" },
    html_url: "https://github.example/repo/commit/81bd20a"
  }
];

const closedIssues = {
  items: [
    {
      number: 42,
      title: "Weekly email summary skips empty weeks",
      labels: [{ name: "bug" }],
      closed_at: "2026-06-02T16:20:00Z",
      user: { login: "pm-user" },
      html_url: "https://github.example/repo/issues/42"
    }
  ]
};

const mergedPrs = {
  items: [
    {
      number: 77,
      title: "Ship board-style weekly report",
      closed_at: "2026-06-02T18:30:00Z",
      user: { login: "maya-dev" },
      html_url: "https://github.example/repo/pull/77"
    }
  ]
};

const claudeResponse = {
  id: "msg_mock_success",
  type: "message",
  role: "assistant",
  model: "claude-sonnet-4-20250514",
  content: [
    {
      type: "text",
      text: "## Executive Pulse\n- The repository had steady delivery activity with 2 commits and 1 merged PR.\n- One customer-facing issue was closed.\n- One hotfix signal should be reviewed after the weekly report.\n\n## Narrative Summary\nThe team shipped a board-style weekly report flow and closed the empty-week summary issue while tightening timezone handling.\n\n## What Shipped\n- PR #77 shipped the board-style weekly report.\n\n## Issues Closed\n- Issue #42 resolved skipped summaries for empty weeks.\n\n## Contributor Spotlight\nMaya and Ari both contributed meaningful delivery work this week.\n\n## Risk Radar\nObserved one hotfix signal in commit 81bd20a; review timezone behavior after deployment.\n\n## Audit Trail\n2 commits, 1 merged PR, 1 closed issue."
    }
  ]
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url || "/", `http://${req.headers.host}`);
  if (req.method === "GET" && url.pathname.includes("/commits")) {
    json(res, commits);
    return;
  }
  if (req.method === "GET" && url.pathname === "/search/issues") {
    const query = url.searchParams.get("q") || "";
    json(res, query.includes("is:pr") ? mergedPrs : closedIssues);
    return;
  }
  if (req.method === "POST" && url.pathname === "/v1/messages") {
    json(res, claudeResponse);
    return;
  }
  if (req.method === "POST" && url.pathname === "/discord") {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", () => {
      received.push(JSON.parse(body || "{}"));
      json(res, { ok: true, received: received.length });
    });
    return;
  }
  if (req.method === "GET" && url.pathname === "/received") {
    json(res, received);
    return;
  }
  json(res, { error: "not found", path: url.pathname }, 404);
});

server.listen(port, () => {
  console.log(`mock execution server listening on http://127.0.0.1:${port}`);
});
