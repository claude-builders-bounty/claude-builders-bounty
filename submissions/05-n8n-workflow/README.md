# 📊 Weekly Dev Summary — n8n + Claude API

Auto-generate a narrative weekly development summary for any GitHub repo, powered by n8n and Claude Sonnet 4.

## How It Works

```
Friday 5pm → Fetch GitHub data (commits/PRs/issues)
                  → Build prompt
                  → Claude API generates narrative
                  → Deliver to Slack/Discord
```

## Setup (5 Steps)

### 1. Install n8n
```bash
# Docker (recommended)
docker run -d --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e N8N_SECURE_COOKIE=false \
  n8nio/n8n

# Or via npm
npm install -g n8n && n8n start
```

### 2. Configure Credentials in n8n

| Credential | Type | Where to Get |
|-----------|------|-------------|
| **GitHub API** | HTTP Header Auth | GitHub → Settings → Developer → Personal Access Token (repo scope) |
| **Claude API** | HTTP Header Auth (`x-api-key`) | [console.anthropic.com](https://console.anthropic.com) → API Keys |

### 3. Import the Workflow
1. Open n8n UI at `http://localhost:5678`
2. Click **Workflows → Import from File**
3. Select `weekly-dev-summary.json`

### 4. Configure Variables
In the **Build Claude Prompt** node, set these at the top of the JavaScript code:

```javascript
const repoUrl = 'https://api.github.com/repos/owner/repo'; // ← YOUR REPO
const language = 'zh'; // 'en' or 'zh'
```

### 5. Activate
Click **Save** → **Active** toggle → Done! ⏰

The workflow runs every Friday at 5PM (configurable in **Weekly Cron Trigger** node).

## Delivery Options

| Channel | Setup | Node |
|---------|-------|------|
| **Slack** | Add Slack credential with webhook URL | `Send to Slack/Discord` |
| **Discord** | Create a webhook in Discord channel settings → Replace the Slack node with HTTP Request to Discord webhook | Modify delivery node |
| **Email** | Add SMTP credential | Replace with `Email` node |

## Sample Output (zh)

```markdown
# 周报：owner/repo (2026-05-25 ~ 2026-05-31)

## 本周概况
本周项目活跃度较高，共 24 个 commit、5 个 PR 合并、3 个 issue 关闭。
主要工作集中在性能优化和新功能开发。

## 关键变更
- **性能优化**: 重构数据库查询层，API 响应时间降低 40%
- **新功能**: 添加用户角色权限系统，支持 RBAC
- **依赖升级**: 升级 Go 1.23，修复 3 个安全漏洞
- **测试覆盖**: 单元测试覆盖率从 62% 提升到 78%

## Bug 修复
- 修复了 WebSocket 连接在弱网环境下的重连问题
- 修复了 CSV 导出时中文字符乱码的 bug
- 修复了 Docker 镜像中时区配置错误

## 下周计划
- 完成 API 文档的 OpenAPI 3.0 规范迁移
- 开始多区域部署方案调研
- 性能基准测试自动化
```

## Environment Variables (n8n)

```
# In n8n → Credentials
GITHUB_TOKEN=ghp_...         # GitHub personal access token
ANTHROPIC_API_KEY=sk-ant-... # Claude API key
```

## Workflow Diagram

```
┌─────────────────┐
│  Cron Trigger   │  Every Friday 5PM
└────────┬────────┘
         ▼
┌─────────────────┐
│ GitHub Commits  │──► Collect Data
├─────────────────┤
│ GitHub PRs      │──► Collect Data
├─────────────────┤
│ GitHub Issues   │──► Collect Data
└────────┬────────┘
         ▼
┌─────────────────┐
│  Merge All Data  │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Build Prompt     │  JavaScript: prepare prompt text
└────────┬────────┘
         ▼
┌─────────────────┐
│ Claude API       │  claude-sonnet-4-20250514
└────────┬────────┘
         ▼
┌─────────────────┐
│ Parse Response   │  Extract Markdown
└────────┬────────┘
         ▼
┌─────────────────┐
│ Slack/Discord    │  Deliver the report
└─────────────────┘
```
