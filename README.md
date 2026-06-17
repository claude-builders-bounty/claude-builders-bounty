# Weekly Dev Summary - n8n Workflow

Generates a narrative summary of GitHub repo activity using the Claude API, delivered every Friday.

## Setup (5 steps)

1. **Import the workflow** — In n8n, go to **Workflows → Import from File** and select `weekly-dev-summary.json`

2. **Set environment variables** in n8n:
   - `GITHUB_REPO` — your repo (e.g., `owner/repo-name`)
   - `GITHUB_TOKEN` — [GitHub PAT](https://github.com/settings/tokens) with `repo` scope
   - `CLAUDE_API_KEY` — your [Anthropic API key](https://console.anthropic.com/)
   - `DESTINATION_WEBHOOK` — Discord/Slack webhook URL or email webhook

3. **Configure delivery** — Replace the webhook URL in the "Send Summary" node with your preferred channel (Discord, Slack, or any webhook-compatible service)

4. **Activate the workflow** — Toggle the workflow on in n8n

5. **Enjoy** — It will run automatically every Friday at 5pm and deliver the summary

## Customization

- **Language**: Change `"en"` to `"fr"` in the Claude API message system prompt
- **Schedule**: Edit the Schedule Trigger node cron expression
- **Output format**: Modify the Claude system prompt for different summary styles

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token
- Claude API key (Anthropic)
- Webhook destination (Discord, Slack, email, etc.)
