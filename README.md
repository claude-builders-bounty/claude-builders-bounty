# n8n + Claude Code 自动化周报

定时生成并发送开发周报，支持 GitHub 数据采集 + Claude AI 总结 + 多渠道分发。

## 功能特性

- ✅ 每周定时触发 (周五 5pm)
- ✅ GitHub 数据采集 (commits, issues, PRs)
- ✅ Claude API 集成生成叙事总结
- ✅ 多渠道发送 (Discord/Slack/Email)
- ✅ 5步快速部署

## 使用步骤

### 1. 导入工作流

1. 打开 n8n 管理界面
2. 点击 "Import from File"
3. 选择 `workflow.json` 文件

### 2. 创建 Credentials

在 n8n 中创建以下 5 个 Credentials：

| Credential | 类型 | 说明 |
|------------|------|------|
| `githubCredentials` | Header Auth | `Authorization: token <GITHUB_TOKEN>` |
| `anthropicApi` | Custom API Key | API Key |
| `discordWebhook` | Webhook URL | Discord Webhook |
| `slackWebhook` | Webhook URL | Slack Webhook |
| `gmailOAuth2` | OAuth2 | Gmail 账号 |

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填写：

```bash
GITHUB_TOKEN=ghp_xxx
OWNER=your-org
REPO=your-repo
ANTHROPIC_API_KEY=sk-ant-xxx
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
EMAIL_FROM=you@gmail.com
EMAIL_TO=team@example.com
```

### 4. 配置节点参数

在工作流中设置以下参数：
- Owner: 你的 GitHub 组织或用户名
- Repo: 仓库名

### 5. 激活工作流

点击 "Activate" 按钮，工作流将在每周五下午 5 点自动运行。

## 文件说明

| 文件 | 说明 |
|------|------|
| workflow.json | n8n 工作流定义 |
| .env.example | 环境变量模板 |
| README.md | 本文档 |

## 自定义

- 修改触发时间：编辑 "Schedule Trigger" 节点
- 修改 prompt：编辑 "Claude Summary" 节点中的 messages
- 添加新渠道：在 "Claude Summary" 后添加新节点

## License

MIT