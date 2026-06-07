# n8n Weekly GitHub Dev Summary 工作流

导入即可用的 n8n 工作流，每周自动生成 GitHub 仓库开发动态报告，由 Claude Sonnet 4 生成叙事性摘要，投递到 Discord/Slack。

## 5步配置

### 1. 导入工作流
- 打开 n8n 编辑器 → **Workflows** → **Import from File**
- 选择 `weekly-dev-summary.json`
- 12 个节点会出现在画布上（含并行 GitHub API + Claude API + Discord）

### 2. 配置认证凭据（3个）
在工作流中设置以下凭据：

| 凭据名称 | 哪里需要 | 从哪里获取 |
|---------|---------|-----------|
| `GitHub Token` | Fetch 节点（Commits / Issues / PRs） | GitHub → Settings → Developer settings → Personal access tokens → `repo` 权限 |
| `Claude API Key` | Call Claude API 节点 | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `Discord Webhook` | Send to Discord 节点 | Discord 频道设置 → Integrations → Webhooks → 新建 |

### 3. 设置配置变量
编辑 **Set Config** 节点，用你实际的值替换：

```
githubRepo:   你的仓库名（如 "owner/repo"）
githubToken:  GitHub personal access token
claudeApiKey: Anthropic API Key
destinationWebhook: Discord Webhook URL
language:     EN 或 FR
```

### 4. 测试运行
- 点 **Manual Trigger (Test)** 节点的 "Execute Node" 按钮
- 观察每个节点绿色通过
- 查看 Discord 频道是否收到了报告

### 5. 激活定时
- 打开 **Schedule Trigger** 节点的激活开关
- 默认每周五 UTC 17:00 自动运行
- 如需改时间，在 Schedule Trigger 节点修改 cron 表达式

## 工作流结构

```
Schedule ─┐
           ├── Set Config → Calc Dates ──┬── Fetch Commits ──┐
Manual ────┘                             ├── Fetch Issues ───┤
                                         └── Fetch PRs ──────┘
                                                    │
                                                    ▼
                                         Merge → Build Prompt → Claude API
                                                    │
                                                    ▼
                                              Format → Send (Discord/Slack)
```

### 节点说明
| 节点 | 作用 |
|------|------|
| Schedule Trigger | UTC 周五 17:00 cron，可改 |
| Manual Trigger | 手动测试用 |
| Set Config | 配置 repo、token、webhook、语言 |
| Calculate Date Range | 自动计算过去 7 天日期范围 |
| Fetch Commits | GitHub API 获取本周 commits |
| Fetch Closed Issues | 获取本周关闭的 issues |
| Fetch Merged PRs | 获取本周合并的 PRs |
| Merge | 合并三个数据源 |
| Build Claude Prompt | 组装 prompt，含数据统计 |
| Call Claude API | 调用 `claude-sonnet-4-20250514` |
| Format Summary | 提取 Claude 输出 |
| Send to Discord | Discord Webhook 投递 |

## 支持的语言
- **EN** — English（默认）
- **FR** — Français（在 Set Config 节点改）

## 示例输出

```
📊 Weekly Dev Summary: claude-builders-bounty/claude-builders-bounty
Period: May 31, 2026 → Jun 7, 2026

This week saw moderate activity with 24 commits, 7 issues closed, and 5 PRs merged.
Notable: the new PR review agent skill was merged, adding automated code review...
```

## 常见问题

**Q: 没有 Discord？可以用 Slack 吗？**
A: 可以。把 **Send to Discord** 节点换成 Slack 节点，或改成任何支持 Webhook 的平台。README 里有 Slack 配置说明。

**Q: 需要安装什么？**
A: 只需要一个 n8n 实例（本地 `npx n8n` 或 n8n.cloud）。工作流本身零依赖。

**Q: Token 安全吗？**
A: n8n 会将凭据加密存储。GitHub Token 只需 `repo` 只读权限，Claude API Key 请确保有对应额度。
