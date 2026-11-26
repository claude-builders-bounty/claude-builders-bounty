#!/usr/bin/env node
// 把工作流里三个 Code 节点的 JS 抽出来，用假数据跑一遍。
// n8n 的 Code 节点跑在 Node 里，只有 $input / $() / $env 这些注入不一样——这里补上同名 shim。
//
// 用法：node validate.mjs
import { readFileSync } from "node:fs";
import vm from "node:vm";
import assert from "node:assert";

const wf = JSON.parse(readFileSync(new URL("./weekly-github-digest.json", import.meta.url), "utf8"));
const codeOf = (name) => {
  const node = wf.nodes.find((n) => n.name === name);
  assert(node, `节点 ${name} 不存在`);
  assert.equal(node.type, "n8n-nodes-base.code", `${name} 不是 Code 节点`);
  return node.parameters.jsCode;
};

// ---- 造一批假的 GitHub 数据 -------------------------------------------------
const commits = Array.from({ length: 70 }, (_, i) => ({
  commit: { author: { name: i % 2 ? "alice" : "bob" }, message: `feat: change number ${i}\n\nbody ignored` },
}));
const prs = Array.from({ length: 12 }, (_, i) => ({ number: 100 + i, title: `Fix flaky test #${i}` }));
const issues = Array.from({ length: 9 }, (_, i) => ({ number: 200 + i, title: `Crash when opening settings (${i})` }));

const claudeReply = {
  stop_reason: "end_turn",
  content: [
    { type: "text", text: "This week the team landed twelve fixes, mostly around flaky tests." },
  ],
};

// ---- n8n 注入的 shim -------------------------------------------------------
function makeCtx({ firstJson, allByNode = {}, env = { SLACK_WEBHOOK_URL: "https://hooks.example/x" } }) {
  const inputFirst = () => ({ json: firstJson });
  const inputAll = () => Object.entries(allByNode).length
    ? Object.entries(allByNode).flatMap(([name, items]) => items.map((json) => ({ json, $nodeName: name })))
    : [{ json: firstJson }];

  const $input = { first: inputFirst, all: inputAll, item: { json: firstJson } };
  const $ = (name) => {
    const items = allByNode[name];
    if (!items) throw new Error(`节点 ${name} 没有数据`);
    return {
      first: () => ({ json: items[0] }),
      all: () => items.map((json) => ({ json })),
      item: { json: items[0] },
    };
  };
  // Bundle 里按键名取别的节点结果；Code 节点之间用 $('Node') 拿到的是上游集合
  return { $input, $, $env: env, console, Date, JSON, Math, String, Number, Object, Array };
}

function runCode(code, ctx) {
  const sandbox = vm.createContext({ ...ctx });
  const script = new vm.Script(`(function(){\n${code}\n})()`, { filename: "code-node.js" });
  return script.runInContext(sandbox);
}

let pass = 0;
const check = (label, fn) => {
  try {
    fn();
    pass += 1;
    console.log(`ok   ${label}`);
  } catch (e) {
    console.log(`FAIL ${label}: ${e.message}`);
    process.exitCode = 1;
  }
};

// ---- 1. Window ------------------------------------------------------------
const cfg = { repo: "n8n-io/n8n", channel: "#dev-digest", language: "EN", days: 7 };
const windowed = runCode(codeOf("Window"), makeCtx({ firstJson: cfg }));
check("Window 算出 7 天窗口 + ISO 串", () => {
  const j = windowed[0].json;
  assert.equal(j.repo, "n8n-io/n8n");
  assert.match(j.since, /^\d{4}-\d{2}-\d{2}T/);
  assert.match(j.sinceDate, /^\d{4}-\d{2}-\d{2}$/);
  const days = (new Date(j.until) - new Date(j.since)) / 86400000;
  assert.ok(Math.abs(days - 7) < 0.01, `窗口应约 7 天，实际 ${days}`);
});

// ---- 2. Bundle ------------------------------------------------------------
// Bundle 用 $('GET commits').all() 拿三路数据，所以按节点名造 shim
const bundleCtx = makeCtx({
  firstJson: windowed[0].json,
  allByNode: {},
});
bundleCtx.$ = (name) => {
  if (name === "Window") return { first: () => ({ json: windowed[0].json }), all: () => [{ json: windowed[0].json }] };
  if (name === "GET merged PRs") return { first: () => ({ json: { items: prs } }), all: () => [{ json: { items: prs } }] };
  if (name === "GET closed issues") return { first: () => ({ json: { items: issues } }), all: () => [{ json: { items: issues } }] };
  if (name === "GET commits") return { first: () => ({ json: commits[0] }), all: () => commits.map((json) => ({ json })) };
  throw new Error(`未知节点 ${name}`);
};
const bundled = runCode(codeOf("Bundle"), bundleCtx);
check("Bundle 计数正确、列表截断到 60/40/40", () => {
  const j = bundled[0].json;
  assert.equal(j.commitCount, 70);
  assert.equal(j.prCount, 12);
  assert.equal(j.issueCount, 9);
  assert.equal(j.commits.split("\n").length, 60, "提交应截断到 60 行");
  assert.equal(j.prs.split("\n").length, 12);
  assert.equal(j.issues.split("\n").length, 9);
  assert.ok(j.commits.includes("feat: change number 0"));
});

// ---- 3. Format ------------------------------------------------------------
const formatCtx = makeCtx({ firstJson: { ...bundled[0].json, channel: "#dev-digest" } });
formatCtx.$ = (name) => {
  if (name === "Bundle") return { first: () => ({ json: bundled[0].json }), all: () => [{ json: bundled[0].json }] };
  throw new Error(`未知节点 ${name}`);
};
// Format 的输入是 Claude 的响应体
formatCtx.$input = { first: () => ({ json: claudeReply }), all: () => [{ json: claudeReply }] };
const formatted = runCode(codeOf("Format"), formatCtx);
check("Format 取出正文并拼标题", () => {
  const j = formatted[0].json;
  assert.match(j.body, /twelve fixes/);
  assert.match(j.title, /^Weekly digest — n8n-io\/n8n/);
  assert.equal(j.channel, "#dev-digest");
});

// ---- 4. Format 的兜底 ------------------------------------------------------
const emptyCtx = makeCtx({ firstJson: bundled[0].json });
emptyCtx.$ = formatCtx.$;
emptyCtx.$input = { first: () => ({ json: { stop_reason: "max_tokens", content: [] } }), all: () => [{ json: { stop_reason: "max_tokens", content: [] } }] };
const fallback = runCode(codeOf("Format"), emptyCtx);
check("Format 空响应时给可读兜底，不发明文", () => {
  const j = fallback[0].json;
  assert.match(j.body, /No narrative returned/);
  assert.match(j.body, /max_tokens/);
  assert.ok(!/twelve fixes/.test(j.body));
});

// ---- 5. 工作流结构 --------------------------------------------------------
check("工作流结构：10 节点、cron 周五 17:00、链路完整", () => {
  assert.equal(wf.nodes.length, 10);
  const cron = wf.nodes.find((n) => n.type === "n8n-nodes-base.scheduleTrigger").parameters.rule.interval[0].expression;
  assert.equal(cron, "0 17 * * 5");
  const chain = ["Weekly (Fri 17:00)", "Config", "Window", "GET commits", "Bundle", "Claude API", "Format", "Slack webhook"];
  for (let i = 0; i < chain.length - 1; i += 1) {
    assert(wf.connections[chain[i]], `${chain[i]} 没有出边`);
  }
  const claude = wf.nodes.find((n) => n.name === "Claude API");
  assert.equal(claude.parameters.url, "https://api.anthropic.com/v1/messages");
  assert.match(claude.parameters.jsonBody, /claude-sonnet-4-20250514/);
});

console.log(`\n${pass} 项通过`);
