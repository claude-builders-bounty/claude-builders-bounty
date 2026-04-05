# 📊 GitHub Weekly Summary with Claude

An n8n workflow that automatically generates weekly narrative summaries of GitHub repository activity using Claude API.

## Features

- 🕐 **Weekly Automation**: Runs every Friday at 5 PM via cron trigger
- 📈 **GitHub Integration**: Fetches commits, closed issues, and merged PRs
- 🤖 **AI-Powered**: Uses Claude API to generate engaging summaries
- 📬 **Multi-Channel Delivery**: Send via Discord webhook or Email
- 🌍 **Multi-Language**: Supports English and French
- ⚙️ **Configurable**: Environment variables for easy customization

## Prerequisites

- n8n instance (cloud or self-hosted)
- GitHub API token
- Anthropic API key
- Discord webhook URL (optional)
- SMTP credentials (optional, for email)

## Setup (5 Steps)

### 1. Import Workflow
```bash
# In n8n, go to Workflows → Import from File
# Select: github-weekly-summary.json
```

### 2. Configure Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_OWNER` | GitHub repository owner | `claude-builders-bounty` |
| `GITHUB_REPO` | GitHub repository name | `claude-builders-bounty` |
| `GITHUB_TOKEN` | GitHub personal access token | `ghp_xxx` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-xxx` |
| `LANGUAGE` | Summary language (EN/FR) | `EN` |
| `DISCORD_WEBHOOK_URL` | Discord webhook (optional) | `https://discord.com/api/webhooks/...` |
| `EMAIL_TO` | Recipient email (optional) | `user@example.com` |

### 3. Set Up GitHub Credentials
- In n8n, go to Settings → Credentials
- Add GitHub OAuth2 or Personal Access Token

### 4. Set Up Anthropic Credentials
- In n8n, go to Settings → Credentials
- Add Anthropic API key

### 5. Activate Workflow
- Toggle the workflow to "Active"
- It will run automatically every Friday at 5 PM

## Workflow Overview

```
┌─────────────────┐
│  Weekly Cron    │ (Friday 5 PM)
└────────┬────────┘
         │
┌────────▼────────┐
│ Calculate Dates │ (Last 7 days)
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    │         │            │
┌───▼───┐ ┌──▼────┐  ┌────▼───┐
│Commits│ │Issues │  │  PRs   │
└───┬───┘ └──┬────┘  └────┬───┘
    │        │            │
    └────┬───┴────────────┘
         │
┌────────▼────────┐
│  Aggregate Data │
└────────┬────────┘
         │
┌────────▼────────┐
│ Claude Summary  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Discord│ │ Email │
└───────┘ └───────┘
```

## Sample Output

```
📊 Weekly Summary - claude-builders-bounty

This week has been productive with 15 commits, 8 closed issues, and 5 merged PRs. 
The team focused on improving the bounty submission process and adding new 
automation features. Notable contributions include the PR review agent and 
weekly summary workflow implementations.

Key highlights:
- 5 new bounties posted
- 3 bounties claimed and completed
- Community engagement increased by 40%
```

## Testing

To test manually:
1. Open the workflow in n8n
2. Click "Execute Workflow"
3. Check Discord channel or email for the summary

## Troubleshooting

| Issue | Solution |
|-------|----------|
| GitHub API rate limit | Use authenticated requests |
| Claude API errors | Check API key and quota |
| Discord not receiving | Verify webhook URL |
| Email not sending | Check SMTP settings |

## License

MIT
