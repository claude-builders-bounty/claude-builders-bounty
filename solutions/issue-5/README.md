# Weekly GitHub Summary - n8n Workflow

Automated weekly dev summary using n8n + Claude API.

## Setup (5 steps)

1. **Import Workflow**
   ```bash
   # Download workflow.json
   # Open n8n → Workflows → Import → Select workflow.json
   ```

2. **Add Credentials**
   - GitHub Token: Create at https://github.com/settings/tokens
   - Anthropic API Key: Create at https://console.anthropic.com
   - Discord Webhook: Create in your Discord server settings

3. **Configure Variables**
   Edit the "Set Variables" node:
   - `repo`: Your GitHub repo (owner/repo)
   - `language`: EN or FR
   - `webhookUrl`: Your Discord webhook URL

4. **Activate Workflow**
   Click "Active" toggle in n8n

5. **Test Run**
   Click "Execute Workflow" button

## Features

- **Trigger**: Weekly cron (Friday 5pm)
- **Data Sources**: GitHub commits, closed issues, merged PRs
- **AI**: Claude Sonnet 4 generates narrative summary
- **Delivery**: Discord webhook (can switch to email/Slack)

## Sample Output

```markdown
📊 Weekly Summary - claude-builders-bounty

This week saw significant progress on the bounty board:
• 5 new PRs submitted for Issues #1-5
• 3 bounties claimed ($275 total)
• New contributors joined the community

Highlights:
- Issue #1 (CHANGELOG generator) received a complete solution
- Issue #4 (PR reviewer) got CLI + GitHub Action implementation

Next week focus: Review pending PRs and add more bounties
```

## Configuration Options

| Variable | Description | Example |
|----------|-------------|---------|
| `repo` | GitHub repository | owner/repo |
| `language` | Summary language | EN / FR |
| `webhookUrl` | Discord webhook | https://discord.com/api/webhooks/... |

## Alternative Delivery

**Email (instead of Discord):**

Replace "Send to Discord" node with:
```json
{
  "name": "Send Email",
  "type": "n8n-nodes-base.emailSend",
  "parameters": {
    "to": "team@example.com",
    "subject": "Weekly GitHub Summary",
    "text": "={{$node['Claude Summary'].json['content'][0]['text']}}"
  }
}
```

**Slack (instead of Discord):**

Replace webhook URL with Slack webhook:
```
https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

## Bounty

Created for [Issue #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

**Amount:** $200 USD