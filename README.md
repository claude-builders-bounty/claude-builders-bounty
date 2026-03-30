# GitHub Weekly Summary - n8n Workflow

Generate weekly narrative summaries of GitHub repository activity using Claude API.

## Features

- **Automated**: Runs every Friday at 5pm via n8n cron trigger
- **Comprehensive**: Fetches commits, closed issues, and merged PRs
- **AI-Powered**: Uses Claude API to generate narrative summaries
- **Multi-channel**: Delivers via Discord webhook (or email)

## 5-Minute Setup

### 1. Import
Open n8n → Settings → Import → Upload `workflow.json`

### 2. Configure Variables
In n8n Variables, set:
- `GITHUB_REPO`: `owner/repo` (your target repository)
- `GITHUB_TOKEN`: GitHub PAT with `repo` scope
- `CLAUDE_API_KEY`: Your Anthropic API key
- `DISCORD_WEBHOOK`: Your Discord webhook URL

### 3. Install Dependencies
In n8n, install these nodes (built-in):
- Schedule Trigger ✅
- HTTP Request ✅  
- Code ✅
- Anthropic (Claude) ✅
- Discord Webhook ✅

### 4. Test
Click "Test Workflow" to verify it works.

### 5. Activate
Toggle workflow ON. It will run every Friday at 5pm automatically.

## Configuration Options

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Target repository | `clawctrl1/changelog-generator` |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxx` |
| `CLAUDE_API_KEY` | Anthropic API Key | `sk-ant-xxx` |
| `DISCORD_WEBHOOK` | Discord webhook URL | `https://discord.com/api/webhooks/xxx` |
| `LANGUAGE` | Summary language | `EN` or `FR` |

## Alternative: Email Delivery

Replace the Discord Webhook node with an Email node:

```
SMTP Host: smtp.gmail.com
SMTP Port: 587
SMTP User: your@gmail.com
SMTP Pass: your-app-password
To: recipient@example.com
Subject: Weekly GitHub Summary for {{$vars.GITHUB_REPO}}
```

## Screenshots

See `screenshots/` folder for:
- Workflow overview
- Successful execution example
- Sample Discord message output

## Support

- n8n Docs: https://docs.n8n.io
- Claude API: https://docs.anthropic.com
- Discord Webhooks: https://support.discord.com/hc/en-us/articles/228383668
