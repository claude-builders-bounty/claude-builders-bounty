// 本地假服务：假装 GitHub + Anthropic + Slack，让整条 n8n 链路能真跑一遍。
// 路由：
//   GET  /repos/:owner/:repo/commits        → 提交列表
//   GET  /search/issues?q=...is:pr...       → 已合并 PR
//   GET  /search/issues?q=...is:issue...    → 已关闭 issue
//   POST /v1/messages                       → Claude 形状的响应
//   POST /slack                             → 收最终 payload，落 received.json
import http from "node:http";
import { writeFileSync } from "node:fs";

const PORT = 8899;

const commits = Array.from({ length: 5 }, (_, i) => ({
  commit: { author: { name: i % 2 ? "alice" : "bob" }, message: `feat: change ${i}\n\nbody` },
}));
const prs = [{ number: 12, title: "Fix flaky scheduling test" }, { number: 15, title: "Add retry to webhook sender" }];
const issues = [{ number: 34, title: "Crash on empty repo" }];

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://127.0.0.1:${PORT}`);
  let body = "";
  req.on("data", (c) => (body += c));
  req.on("end", () => {
    const json = (code, data) => {
      res.writeHead(code, { "content-type": "application/json" });
      res.end(JSON.stringify(data));
    };

    if (url.pathname.endsWith("/commits")) return json(200, commits);
    if (url.pathname === "/search/issues") {
      const q = url.searchParams.get("q") || "";
      return json(200, { total_count: q.includes("is:pr") ? prs.length : issues.length, items: q.includes("is:pr") ? prs : issues });
    }
    if (url.pathname === "/v1/messages") {
      return json(200, {
        stop_reason: "end_turn",
        content: [{ type: "text", text: "This week the team shipped a retry path for the webhook sender and fixed a flaky scheduling test, plus a crash on empty repositories." }],
      });
    }
    if (url.pathname === "/slack") {
      writeFileSync(new URL("./received.json", import.meta.url), body || "{}");
      console.log(`slack payload ${body.length} bytes`);
      return json(200, { ok: true });
    }
    json(404, { error: "not found", path: url.pathname, q: url.search });
  });
});

server.listen(PORT, "127.0.0.1", () => console.log(`fake api on http://127.0.0.1:${PORT}`));
setTimeout(() => server.close(), 180000);
