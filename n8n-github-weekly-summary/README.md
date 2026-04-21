# 📊 GitHub Weekly Summary with Claude - n8n Workflow

Automatically generate narrative weekly summaries of GitHub repository activity using n8n and Claude API.

![Bounty](https://img.shields.io/badge/Bounty-%24200-success)
![n8n](https://img.shields.io/badge/n8n-workflow-red)
![Claude](https://img.shields.io/badge/Claude-sonnet--4-orange)

## 🎯 Features

- ⏰ **Weekly Trigger**: Every Friday at 5:00 PM (configurable)
- 📈 **GitHub Data**: Fetches commits, closed issues, and merged PRs
- 🤖 **AI Summary**: Uses Claude API (claude-sonnet-4-20250514) for narrative generation
- 📬 **Multi-Channel**: Delivers via Discord webhook or Email (SendGrid)
- 🔧 **Configurable**: Environment variables for easy customization

## 🚀 Setup Instructions (5 Steps)

### Step 1: Import the Workflow

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `workflow.json`
4. Click **Import**

### Step 2: Configure Environment Variables

Set the following environment variables in n8n (**Settings** → **Environment Variables**):

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token (repo scope) | `ghp_xxxxx` |
| `GITHUB_REPO_URL` | GitHub API URL for your repo | `https://api.github.com/repos/owner/repo` |
| `GITHUB_REPO_NAME` | Human-readable repo name | `owner/repo` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-xxxxx` |
| `SUMMARY_LANGUAGE` | Summary language (EN/FR/etc.) | `English` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL (optional) | `https://discord.com/api/webhooks/...` |
| `SENDGRID_API_KEY` | SendGrid API key (for email) | `SG.xxxxx` |
| `RECIPIENT_EMAIL` | Email recipient | `team@example.com` |
| `FROM_EMAIL` | Email sender | `noreply@example.com` |

### Step 3: Create GitHub Personal Access Token

1. Go to GitHub **Settings** → **Developer settings** → **Personal access tokens**
2. Click **Generate new token (classic)**
3. Select scopes: `repo` (full control of private repositories)
4. Copy the token and save it as `GITHUB_TOKEN` environment variable

### Step 4: Get Anthropic API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Save it as `ANTHROPIC_API_KEY` environment variable

### Step 5: Configure Output Channel

**For Discord:**
1. Go to your Discord server **Settings** → **Integrations** → **Webhooks**
2. Create a new webhook
3. Copy the webhook URL
4. Set as `DISCORD_WEBHOOK_URL` environment variable
5. Disable the "Send Email" node in n8n (click the node, press `Ctrl+E`)

**For Email:**
1. Sign up at [SendGrid](https://sendgrid.com/)
2. Create an API key
3. Set `SENDGRID_API_KEY`, `RECIPIENT_EMAIL`, and `FROM_EMAIL` environment variables
4. Disable the "Send to Discord" node in n8n (click the node, press `Ctrl+E`)

## 📋 Workflow Architecture

```
┌─────────────────┐
│ Schedule Trigger │ (Every Friday 17:00)
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    │         │            │
┌───▼───┐ ┌──▼────┐ ┌────▼────┐
│Commits│ │Issues │ │  PRs    │
└───┬───┘ └───┬───┘ └────┬────┘
    │         │          │
    └────┬────┴──────────┘
         │
    ┌────▼────┐
    │  Merge  │
    └────┬────┘
         │
    ┌────▼────┐
    │ Prepare │
    │ Prompt  │
    └────┬────┘
         │
    ┌────▼────┐
    │ Claude  │
    │  API    │
    └────┬────┘
         │
    ┌────▼────┐
    │ Extract │
    └────┬────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Discord│ │ Email │
└───────┘ └───────┘
```

## 🧪 Testing

1. In n8n, click **Execute Workflow** button
2. Wait for all nodes to complete (green checkmarks)
3. Check your Discord channel or email for the summary
4. Review the execution log for any errors

### Sample Output

```
📊 Weekly GitHub Summary

This week saw impressive activity in owner/repo! 🚀

Top contributor @dev1 led with 15 commits, including the highly 
anticipated authentication refactor. The team closed 8 issues, 
notably fixing the critical memory leak (#234). Three PRs were 
merged, with #456 standing out as a major performance improvement.

Key highlights:
- New feature: Dark mode support
- Bug fixes: 5 critical issues resolved
- Code quality: Test coverage increased to 87%

Great work team! 👏
```

## 🔧 Customization

### Change Schedule

Edit the **Schedule Trigger** node:
- Click the node
- Modify the cron expression or use the UI builder
- Examples:
  - Every Monday 9:00 AM: `0 9 * * 1`
  - Every day at 18:00: `0 18 * * *`

### Change Language

Set `SUMMARY_LANGUAGE` environment variable:
- `English` - English summary
- `Français` - French summary
- `Español` - Spanish summary
- `中文` - Chinese summary

### Add More Data Sources

You can extend the workflow to include:
- GitHub Releases
- Discussion activity
- Star count changes
- Contributor statistics

## 📝 Notes

- The workflow fetches data for the **last 7 days** from execution time
- Rate limits: GitHub API (5000 req/hour), Anthropic API (varies by plan)
- Maximum items per fetch: 100 (adjustable in query parameters)
- Summary length: ~300-500 words (configurable in prompt)

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| GitHub API 401 | Check `GITHUB_TOKEN` is valid and has `repo` scope |
| Claude API 401 | Verify `ANTHROPIC_API_KEY` is correct |
| Discord webhook fails | Ensure webhook URL is valid and not expired |
| Email not sent | Check SendGrid API key and sender domain verification |
| No data returned | Verify repo URL and that activity exists in the time range |

## 📄 License

MIT License - Feel free to use and modify for your bounty submission!

## 🎁 Bounty Info

This workflow was created for the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) program.

**Bounty Amount:** $200  
**Status:** Ready for submission ✅
