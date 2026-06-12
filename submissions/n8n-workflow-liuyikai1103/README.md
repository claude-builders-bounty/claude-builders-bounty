# n8n Weekly Dev Summary — Claude + GitHub

> 每周自动生成 GitHub 仓库活动摘要，通过 Claude AI 生成叙事性周报

## 安装 (5步)

### 1. 导入工作流
- 打开 n8n → **Workflows** → **Import from File**
- 选择 `n8n_weekly_summary.json`

### 2. 配置 GitHub Token
- 创建一个 [GitHub Personal Access Token](https://github.com/settings/tokens) (`repo` 权限)
- 在 n8n 中创建 **Generic Credential** → `httpHeaderAuth`
- Header Name: `Authorization`, Header Value: `Bearer YOUR_TOKEN`

### 3. 配置 Claude API Key
- 获取 [Anthropic API Key](https://console.anthropic.com/)
- 在 n8n 中创建 **Header Auth** 凭证
- Header Name: `x-api-key`, Value: `sk-ant-...`

### 4. 配置目标仓库
- 编辑第一个 HTTP Request 节点
- 将 `={{ $json.repo_url }}` 改为实际的 API 路径
- 例如: `https://api.github.com/repos/owner/repo`

### 5. 配置 Slack Webhook (或邮件)
- Slack: 创建 Incoming Webhook → 将 URL 填入最后一个节点
- 邮件: 用 n8n 的 Email 节点替换最后一个节点

## 配置变量

| 变量 | 位置 | 说明 |
|------|------|------|
| repo_url | 各 HTTP 节点 | GitHub API 仓库路径 |
| github_token | Credential | GitHub 认证 |
| claude_api_key | Credential | Claude/Anthropic API |
| webhook_url | 发送节点 | Slack/Discord/Teams |
| language | Prompt 节点 | EN / FR / ZH 等 |

## 触发时间

每周五 17:00 (时区: Asia/Shanghai)，可在 Schedule Trigger 节点修改。

## 示例输出

```
## Weekly Dev Summary

### Executive Summary
This week saw 23 commits, 5 closed issues, and 3 merged PRs...

### Key Changes
- Added user authentication flow
- Fixed database connection pooling issue
- Updated API documentation

### Bugs Fixed
- #123 Login timeout on mobile
- #124 Data race in cache layer

### Looking Ahead
Next sprint focuses on performance optimization...
```
