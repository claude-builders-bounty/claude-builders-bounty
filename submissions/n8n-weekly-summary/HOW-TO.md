# How-To Guide: n8n Weekly Dev Summary Workflow

## Importing the Workflow

1. Open your n8n instance (self-hosted or n8n.cloud)
2. Click **"Add workflow"** in the top right
3. Click **"Import from file"**
4. Select `workflow.json`
5. The workflow appears with all 10 nodes connected

## Setting Up Credentials

### GitHub Token
1. Go to https://github.com/settings/tokens
2. Generate a token with `repo` scope
3. In n8n: Settings > Credentials > New > **Header Auth**
4. Name: `GitHub Token`
5. Header: `Authorization`, Value: `Bearer ghp_your_token`

### Anthropic API Key
1. Get key from https://console.anthropic.com
2. In n8n: Settings > Credentials > New > **Header Auth**
3. Name: `Anthropic API Key`
4. Header: `x-api-key`, Value: `sk-ant-your_key`

### Discord Webhook
1. In Discord: Server Settings > Integrations > Webhooks > New
2. Copy the webhook URL
3. Set as `DISCORD_WEBHOOK_URL` in n8n variables

### Slack Webhook (optional)
1. Create a Slack app at https://api.slack.com/apps
2. Add Incoming Webhooks
3. Copy the webhook URL
4. Set as `SLACK_WEBHOOK_URL` in n8n variables

## Customization

### Change the schedule
Click the **Weekly Trigger** node and adjust:
- `triggerAtDay`: 0=Sun, 1=Mon ... 5=Fri, 6=Sat
- `triggerAtHour`: 0-23 (UTC)

### Change the language
Set `SUMMARY_LANGUAGE` variable to:
- `EN` — English (default)
- `FR` — French

### Change the repo
Set `GITHUB_REPO` variable to any public or private repo: `owner/repo`

### Change the Claude model
In the **Call Claude API** node, change the model in the JSON body:
- `claude-sonnet-4-20250514` (default, best balance)
- `claude-opus-4-20250514` (higher quality, slower)
- `claude-haiku-4-5-20251001` (faster, cheaper)

### Add email delivery
Add an **Email Send** node after **Format Summary** and connect it. Configure with your SMTP credentials.

## Testing

1. Click **"Execute Workflow"** (play button) to run immediately
2. Check each node's output by clicking on it
3. Verify the Discord/Slack message arrived
4. If errors: check credentials and environment variables

## Troubleshooting

**"401 Unauthorized" on GitHub nodes**
- Check your GitHub token has `repo` scope
- Verify the Header Auth credential uses `Authorization` header with `Bearer ` prefix

**"401" on Claude API**
- Check the Anthropic key is valid
- Verify the Header Auth uses `x-api-key` header (no Bearer prefix)

**"No summary generated"**
- The repo might have zero activity in the last 7 days
- Try a more active repo for testing

**Discord message truncated**
- Discord has a 2000-char limit. The workflow auto-truncates.
- For longer summaries, consider using Discord embeds or multiple messages.
