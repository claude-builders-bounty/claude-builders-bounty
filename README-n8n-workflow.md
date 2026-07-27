# Weekly GitHub Summary — n8n + Claude AI Workflow

Automatically generates a weekly narrative summary of any GitHub repo's activity using Claude API, delivered via Discord webhook (configurable for Slack or email).

## Quick Setup (5 Steps)

### 1. Import the Workflow
In n8n, go to **Workflows → Import from File** and select `weekly-github-summary.json`.

### 2. Configure Variables
Open each **Set** node and update:
| Node | Variable | Example |
|------|----------|---------|
| Set Repo Info | `repo_owner` | `claude-builders-bounty` |
| Set Repo Info | `repo_name` | `claude-builders-bounty` |
| Set Repo Info | `github_token` | `ghp_xxxx` (fine-grained PAT with `contents:read`, `issues:read`, `pull_requests:read`) |
| Set Language | `language` | `EN` or `FR` |
| Set Webhook URL | `webhook_url` | Your Discord/Slack webhook URL |

### 3. Configure Claude API Credential
Click the **Claude API** node → Credentials → Add your Anthropic API key.

### 4. Test Once
Click **Execute Workflow** to verify it fetches your repo data and generates a summary.

### 5. Activate
Toggle **Active** (top-right) to enable the weekly cron (Fridays at 5pm).

## How It Works

```
[Cron: Friday 5pm]
        │
        ├──→ [Fetch Commits] ──→ [Merge] ──→ [Prepare Prompt] ──→ [Claude API] ──→ [Discord Webhook]
        ├──→ [Fetch Issues]  ──→
        └──→ [Fetch PRs]    ──→
```

1. **Schedule Trigger**: fires every Friday at 17:00
2. **GitHub API calls**: fetches commits, closed issues, and merged PRs from the past 7 days
3. **Merge**: combines all data streams
4. **Prepare Prompt**: code node builds a structured prompt with repo activity
5. **Claude API**: generates a 3-5 paragraph narrative summary
6. **Discord Webhook**: delivers the summary to your team channel

## Customization

### Change Delivery Channel
- **Slack**: swap the webhook URL and update the body format in `Send via Discord Webhook` node
- **Email**: replace with n8n's built-in Email node (SMTP)
- **Telegram**: replace with Telegram node

### Change Schedule
Edit the cron expression in `Schedule Trigger`:
- `0 9 * * 1` = Monday 9am
- `0 17 * * *` = Every day 5pm
- `0 8 * * 1-5` = Weekdays 8am

### Add More Data Sources
Extend the workflow by adding HTTP Request nodes for:
- GitHub Releases API (`/releases`)
- GitHub Stargazers API (`/stargazers`)
- GitHub Actions runs (`/actions/runs`)

## Requirements
- n8n instance (self-hosted or n8n.cloud)
- GitHub fine-grained PAT with repo read permissions
- Anthropic API key (Claude)
- Discord webhook URL (or alternative delivery target)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Empty commits list | Check token has `contents:read` scope |
| Claude timeout | Increase `maxTokens` or reduce commit count in code node `.slice(0,15)` |
| Webhook 400 | Verify webhook URL format and payload structure |
| `$now.minus` not working | Use n8n Date & Time node instead of expression |
