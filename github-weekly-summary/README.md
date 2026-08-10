# GitHub Weekly Dev Summary — n8n + Claude 工作流

每周五 17:00 自动抓取仓库本周 commits / 已关闭 issues / merged PRs，交给 Claude（`claude-sonnet-4-20250514`）生成叙事化周报，推送到 Slack/Discord Webhook。

## 安装（5 步）

1. n8n 中导入 `github-weekly-summary.json`（工作流 → 导入）。
2. 配置环境变量（工作流设置 → Environment）：
   - `GITHUB_TOKEN`：GitHub 个人令牌（`repo` 权限）
   - `ANTHROPIC_API_KEY`：Claude API Key
   - `DELIVERY_WEBHOOK`：Slack/Discord Webhook URL
   - `GITHUB_REPO`：仓库，如 `owner/repo`（可选，默认在配置节点改）
   - `SUMMARY_LANG`：`EN` 或 `FR`（可选，默认 EN）
3. 确认「每周五 17:00 触发」节点的 cron（默认 `0 17 * * 5`）。
4. 测试：点击工作流右上角「执行」，检查 Claude 节点与 Webhook 节点输出。
5. 激活「Active」开关，之后每周五自动运行。

## 变量说明

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `GITHUB_TOKEN` | 是 | GitHub API 令牌 |
| `ANTHROPIC_API_KEY` | 是 | Anthropic Claude API Key |
| `DELIVERY_WEBHOOK` | 是 | Slack/Discord Incoming Webhook |
| `GITHUB_REPO` | 否 | 仓库 `owner/repo`（默认在配置节点填写） |
| `SUMMARY_LANG` | 否 | 输出语言 `EN`/`FR` |

> 注：本机暂未部署真实 n8n 实例，工作流按 n8n 1.x 规范编写；导入后请先手动执行一次验证再开启定时。
