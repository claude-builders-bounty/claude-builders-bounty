# Weekly Dev Summary - n8n Workflow

Automated weekly GitHub repository activity summaries using n8n + Claude API.

## 🚀 Quick Setup (5 Steps)

### 1. Import the Workflow

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `weekly-dev-summary-workflow.json`

### 2. Configure Credentials

Add these credentials in n8n (**Settings** → **Credentials**):

| Credential | Type | Value |
|------------|------|-------|
| `github-credentials` | GitHub API | Your GitHub personal access token |
| `claude-api-credentials` | Anthropic API | Your Claude API key |
| `discord-credentials` (optional) | Discord Webhook | Your Discord webhook URL |
| `slack-credentials` (optional) | Slack API | Your Slack bot token |

### 3. Set Environment Variables

In your n8n instance, set these variables (**Settings** → **Variables**):

```
GITHUB_OWNER=your-github-username-or-org
GITHUB_REPO=your-repo-name
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SUMMARY_EMAIL_RECIPIENT=your-email@example.com
```

### 4. Activate the Workflow

1. Toggle the workflow to **Active**
2. The workflow will run every Friday at 5 PM

### 5. Test It

1. Click **Execute Workflow** to test manually
2. Check your Discord/Slack/Email for the summary

## 📋 What It Does

Every Friday at 5 PM, the workflow:

1. **Fetches GitHub data** from the past week:
   - Commits
   - Closed issues
   - Merged PRs

2. **Aggregates the data** into a structured summary

3. **Generates a narrative summary** using Claude API

4. **Delivers the summary** via:
   - Discord webhook
   - Slack message
   - Email

## 🔧 Customization

### Change the Schedule

Edit the **Cron** node:
- Default: `0 17 * * 5` (Friday 5 PM)
- Format: [cron expression](https://crontab.guru/)

### Change the Language

Edit the **Generate Summary with Claude** node:
- Default: English
- Modify the system prompt for other languages

### Add More Outputs

Add nodes after **Generate Summary with Claude**:
- Telegram
- Microsoft Teams
- Webhook
- Database

## 🐛 Troubleshooting

### Workflow not triggering?
- Check if the workflow is **Active**
- Verify the cron expression

### GitHub API errors?
- Check your GitHub token has `repo` scope
- Verify `GITHUB_OWNER` and `GITHUB_REPO` variables

### Claude API errors?
- Check your Anthropic API key
- Verify you have API credits

### No messages received?
- Check webhook URLs are correct
- Verify email settings in n8n

## 📄 License

MIT - Feel free to use and modify.

---

**Created for:** claude-builders-bounty Issue #5  
**Bounty:** $200 USD via Opire