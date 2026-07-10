# Weekly GitHub Dev Summary (Claude) — Bounty #5

> 对应赏金：[claude-builders-bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)
> 赏金：**$200（Opire，合并后 USDT 支付）**
> 交付物：`Weekly-GitHub-Dev-Summary.workflow.json`（可直接导入 n8n 的工作流）+ 本文档。

一个完全自包含的 n8n 工作流：每周自动拉取 GitHub 仓库的 commits / 已关闭 issues / 已合并 PRs，调用 Claude（`claude-sonnet-4-20250514`）生成叙述性周报，并通过 Slack/Discord webhook 投递。

---

## ✅ 验收标准逐条对照

| 验收要求 | 实现方式 |
|----------|----------|
| 可导出的 n8n 工作流（`.json`） | `Weekly-GitHub-Dev-Summary.workflow.json`，n8n 可直接 Import |
| 触发：每周 cron（如周五 17:00） | `Weekly Trigger` 节点，`dayOfWeek:[5]`（周五），17:00 |
| 拉取 GitHub API：本周 commits / 已关闭 issues / 已合并 PRs | `Get Commits` / `Get Closed Issues` / `Get Merged PRs` 三个 HTTP Request 直连 REST |
| 调用 Claude API（`claude-sonnet-4-20250514`）生成叙述性周报 | `Generate Summary (Claude)` 节点 POST `/v1/messages` |
| 投递：email **或** Discord/Slack webhook（自选并文档化） | `Deliver (Slack/Discord)` 节点，兼容 Slack(`text`) 与 Discord(`content`) 两种格式 |
| 可配置：GitHub 仓库 / 目标渠道 / 语言（EN/FR） | 全部走环境变量（见下），无需改工作流 |

---

## 🔧 配置（环境变量）

在 n8n 的 **Settings → Environment** 中设置：

| 变量 | 说明 | 示例 |
|------|------|------|
| `GH_OWNER` | 仓库 owner | `anthropics` |
| `GH_REPO` | 仓库名 | `claude-code` |
| `GITHUB_TOKEN` | 有 `repo` 读权限的 GitHub PAT | `ghp_xxx` |
| `ANTHROPIC_API_KEY` | Anthropic API Key | `sk-ant-xxx` |
| `DELIVERY_WEBHOOK` | Slack 或 Discord 入站 webhook URL | `https://hooks.slack.com/...` |
| `LANG` | 周报语言，`EN` 或 `FR` | `EN` |

> 所有密钥均通过 `{{ $env.* }}` 引用，**工作流内不含任何明文密钥**，导入即可用。

---

## 🚀 使用步骤

1. n8n 中 **Workflows → Import from File**，选择 `Weekly-GitHub-Dev-Summary.workflow.json`。
2. 在 n8n 设置好上述 6 个环境变量。
3. 点击 **Execute Workflow** 手动跑一次验证；确认无误后开启 **Active**（周五 17:00 自动执行）。

---

## 🔍 工作流结构

```
Weekly Trigger (Cron, 周五17:00)
        │
     Config (Set: owner/repo/lang/since)
        │
        ├─ Get Commits ─────┐
        ├─ Get Closed Issues ─┤
        └─ Get Merged PRs ───┤
                              ▼
                   Build Prompt (Code: 汇总三路数据为 prompt)
                              │
                   Generate Summary (Claude /v1/messages)
                              │
                       Format Summary (Set)
                              │
                   Deliver (Slack/Discord webhook)
```

- **Build Prompt** 会过滤 `issues` 接口返回的 PR（GitHub issues API 会混入 PR），并按 `LANG` 决定中英/法语指令。
- **Deliver** 同时发送 `text` 与 `content` 字段，兼顾 Slack 与 Discord webhook 格式。

---

## 📝 领取与提交（由需求方执行）

1. 在 issue #5 下评论 `/opire try` 认领。
2. Fork 本仓库，将 `bounty-5-weekly-dev-summary/` 放入你的 fork。
3. 提交 PR，等待合并；Opire 在合并后自动以 USDT（TRC20）发放 $200。
