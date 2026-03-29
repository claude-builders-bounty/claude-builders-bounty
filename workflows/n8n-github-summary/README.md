# GitHub Weekly Dev Summary with Claude

Automatically generates a narrative summary of your GitHub repository's weekly activity using Claude AI and delivers it via Discord webhook.

## Features

- 🕒 **Weekly cron trigger** (Friday at 5pm)
- 📊 **Comprehensive data collection**: commits, closed issues, merged PRs
- 🤖 **AI-powered narrative** using Claude Sonnet 4
- 🔔 **Discord webhook delivery** with rich embeds
- 🌍 **Multi-language support** (EN/FR configurable)
- ⚙️ **Fully configurable** via environment variables

## Quick Setup (5 Steps)

### 1. Import the Workflow
- In n8n, go to **Workflows** → **Import from File**
- Select `workflow.json`
- Click **Import**

### 2. Set Environment Variables
Add these to your n8n environment (`.env` or Settings → Variables):

```bash
GITHUB_REPO=owner/repo           # Your GitHub repository (e.g., "anthropics/anthropic-sdk-python")
GITHUB_TOKEN=ghp_xxxx            # GitHub Personal Access Token with 'repo' scope
CLAUDE_API_KEY=sk-ant-xxxx       # Anthropic API key
WEBHOOK_URL=https://discord.com/api/webhooks/xxx  # Discord webhook URL
LANGUAGE=EN                      # EN or FR (optional, defaults to EN)
```

**Getting tokens:**
- **GitHub Token**: https://github.com/settings/tokens → Generate new token (classic) → Select `repo` scope
- **Claude API Key**: https://console.anthropic.com/settings/keys
- **Discord Webhook**: Server Settings → Integrations → Webhooks → New Webhook → Copy URL

### 3. Configure Credentials
The workflow uses HTTP Header Authentication for APIs:

**For GitHub API:**
- Go to **Credentials** → **Add Credential** → **Header Auth**
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer YOUR_GITHUB_TOKEN`

**For Claude API:**
- Go to **Credentials** → **Add Credential** → **Header Auth**
- Name: `Claude API Key`
- Header Name: `x-api-key`
- Header Value: `YOUR_CLAUDE_API_KEY`

### 4. Test the Workflow
- Open the workflow
- Click **Execute Workflow** (top right)
- Check Discord for the summary message

### 5. Activate the Schedule
- Toggle **Active** switch (top right)
- The workflow will now run every Friday at 5pm

## Example Output

The Discord message will contain:

```
📊 Weekly Dev Summary: anthropics/anthropic-sdk-python

This week saw strong activity with 23 commits, 5 closed issues, and 3 merged pull requests.

**Key Highlights:**
- Added streaming support for messages API (#145)
- Fixed token counting bug in embeddings (#142)
- Updated documentation for vision capabilities

**Bug Fixes:**
- Resolved timeout issues in long-running requests
- Fixed type hints for async client methods

**Contributors:** @dev1, @dev2, @dev3

Week of 3/22/2026
```

## Customization

### Change Schedule
Edit the **Weekly Trigger** node:
- Current: `0 17 * * 5` (Friday 5pm)
- Daily: `0 17 * * *`
- Monthly: `0 17 1 * *`

### Email Delivery Instead
Replace the **Send to Discord** node with n8n's **Email** node:
- Subject: `Weekly Dev Summary: {{ $json.repo }}`
- Body: `{{ $json.content }}`

### Slack Delivery
Replace the webhook URL with a Slack webhook and adjust the payload format.

## Troubleshooting

**Rate limits:** GitHub API has a rate limit of 5000 requests/hour for authenticated users. This workflow uses 3 requests per execution.

**Large repositories:** If you have >100 commits/week, the workflow may hit pagination limits. Adjust `per_page` in the HTTP Request nodes.

**Language support:** Currently supports EN (English) and FR (French). To add more languages, update the prompt in the **Claude API** node.

## Technical Details

- **Model:** `claude-sonnet-4-20250514`
- **Max tokens:** 2048
- **Data retention:** Last 7 days of activity
- **Execution time:** ~5-10 seconds per run

## License

MIT - Feel free to modify and reuse!

---

**Bounty submission for:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5
