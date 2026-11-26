# 测试记录（2026-11-26）

环境：Windows 11 / Node v24.21.0 / **n8n 2.49.7**（`npm i n8n`，本地实例，`N8N_USER_FOLDER` 指向临时目录）。

目标：不是“看着像能跑”，而是把它塞进真 n8n，跑出 `status: success`。

## 1. 真实例导入

```console
$ n8n import:workflow --input=weekly-github-digest.json
Importing 1 workflows...
Successfully imported 1 workflow.

$ n8n list:workflow
6VFJ0TS3xaCtPLmK|weekly-github-digest
```

导入不改一个字段，说明节点类型、typeVersion、连接结构都合规。

## 2. 端到端执行（本地假服务替代三个外部依赖）

没有 Anthropic key、也没有 Slack workspace，所以把三处外部依赖指向本地假服务
（`fake-api.mjs`，同时扮演 GitHub / Anthropic / Slack），其余节点一个没改：

```console
$ node fake-api.mjs      # 127.0.0.1:8899
$ SLACK_WEBHOOK_URL=http://127.0.0.1:8899/slack \
  N8N_BLOCK_ENV_ACCESS_IN_NODE=false \
  n8n execute --id <id>

  "status": "success"
```

假 Slack 收到的内容：

```json
{"text":"*Weekly digest — n8n-io/n8n (2026-11-19 → 2026-11-26)*\n\nThis week the team shipped a retry path for the webhook sender and fixed a flaky scheduling test, plus a crash on empty repositories.\n\n_5 commits · 2 merged PRs · 1 closed issues_"}
```

数字与假数据一致：5 条提交、2 个已合并 PR、1 个已关闭 issue。

## 3. 真机跑出来才发现的三个 bug

这三处都是纸上看不出来、`n8n execute` 一跑就现形的：

1. **`$('节点')` 在分支没跑时直接抛错**
   `Node 'GET merged PRs' hasn't been executed` —— 某周没有合并 PR 时整条流会挂。
   改成 `safe()` 包裹，取不到就返回空数组。

2. **搜索接口返回多条 item 时只数了第一条**
   `.items` 直接取第一个，导致 2 个 PR 只算 1 个。改成 `flatMap(r => r.items || [])`。

3. **`$env` 默认被禁用**
   `access to env vars denied`。要么设 `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`，要么别用环境变量。
   选了前者，并写进 README 第 3 步——不写这一步，别人装完必踩。

## 4. 代码节点单测

`node validate.mjs` 把三个 Code 节点的 JS 抽出来，用 n8n 同名 shim（`$input` / `$()` / `$env`）跑：

```console
ok   Window 算出 7 天窗口 + ISO 串
ok   Bundle 计数正确、列表截断到 60/40/40
ok   Format 取出正文并拼标题
ok   Format 空响应时给可读兜底，不发明文
ok   工作流结构：10 节点、cron 周五 17:00、链路完整

5 项通过
```

## 没做的部分

- 没有真的打 Anthropic API（没有 key），也没有真 Slack（没有 workspace）。这两段用本地假服务验证了“形状与衔接”，没有验证“真实服务的返回格式是否完全一致”。Antthropic 的 `content[].text` 是按官方文档写的，但我没亲眼见过真实响应。
- 没有截图：n8n 的 CLI 执行是我这里的验证方式，没有开浏览器点界面。
