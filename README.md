# n8n + Claude Weekly Dev Summary

Automated weekly GitHub activity summary using n8n workflow and Claude API.

## Quick Start (5 Steps)

### 1. Deploy n8n
```bash
docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n
```

### 2. Import Workflow
Import `n8n-workflow.json` via **Menu → Import from File**.

### 3. Configure Credentials
Add credentials in **Settings → Credentials**:
- **GitHub API**: Personal Access Token (scope: `repo`)
- **Anthropic API**: Your API key

### 4. Set Parameters
Click the **Cron** node and set:
- `repo`: Your GitHub repo (e.g., `owner/repo-name`)
- `lang`: `EN` or `FR`
- `webhookUrl`: Slack/Discord incoming webhook URL

### 5. Test
Toggle workflow ON → **Execute Workflow**. Check your channel.

## How It Works

```
Cron (Friday 5pm) → GitHub API (commits/issues/PRs)
                 → Claude API (generate summary)
                 → Webhook (Slack/Discord)
```

## Configurable Variables

| Variable   | Description           | Example            |
|------------|-----------------------|--------------------|
| `repo`     | GitHub repository     | `owner/my-project` |
| `lang`     | Summary language      | `EN` or `FR`       |
| `webhookUrl` | Delivery webhook    | `https://hooks.slack.com/...` |

## Delivery Options

- **Slack**: Use Slack Incoming Webhook URL
- **Discord**: Use Discord Webhook URL
- **Email**: Replace webhook node with Gmail/SMTP node

## Requirements

- n8n v1.0+
- GitHub Personal Access Token
- Anthropic API Key
- Active webhook endpoint (Slack/Discord)

## Notes

- Workflow runs every Friday at 5:00 PM
- Fetches activity from the past 7 days
- Claude model: `claude-sonnet-4-20250514`
