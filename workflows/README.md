# 📊 Weekly GitHub Dev Summary — n8n + Claude API

Automatically generates a weekly narrative summary of GitHub repo activity using Claude.

## Setup (5 steps)

### 1. Import Workflow
Open n8n → Workflows → Import from File → select `weekly-dev-summary.json`

### 2. Set Variables
In n8n Settings → Variables, create:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_OWNER` | Repo owner | `octocat` |
| `GITHUB_REPO` | Repo name | `hello-world` |
| `GITHUB_TOKEN` | GitHub PAT | `ghp_xxxx` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-xxxx` |
| `WEBHOOK_URL` | Discord/Slack webhook | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Output language (optional) | `EN` or `FR` |

### 3. Configure Schedule
Default: Every Friday at 5pm. Edit the trigger node to change.

### 4. Set Webhook URL
Supports:
- Discord: `https://discord.com/api/webhooks/{id}/{token}`
- Slack: `https://hooks.slack.com/services/{path}`

### 5. Activate
Toggle the workflow to Active. It will run every Friday.

## What It Does

1. **Fetches** commits, merged PRs, and closed issues from the past week
2. **Summarizes** using Claude API (`claude-sonnet-4-20250514`)
3. **Delivers** a narrative summary via Discord/Slack webhook

## Output Example

```
## 📊 Weekly Dev Summary — octocat/hello-world

### Highlights
- Major refactor of authentication system (PR #42)
- 15 commits from 3 contributors

### Commits
- fix: resolve login timeout issue (abc1234)
- feat: add dark mode support (def5678)

### PRs Merged
- #42: Refactor auth to use JWT (@octocat)
- #41: Add unit tests (@contributor)

### Issues Closed
- #38: Login timeout on mobile
- #37: Dark mode request

### Next Week Outlook
- Focus on performance optimization
- Mobile responsive design
```

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token (read access)
- Anthropic API key
- Discord or Slack webhook URL
