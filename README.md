# Weekly Dev Summary — n8n Workflow

Generate a weekly narrative summary of GitHub repo activity using Claude API, delivered to Slack.

## Setup (5 steps)

1. **Import** — In n8n, go to **Workflows → Import from File** and select weekly-dev-summary.json
2. **Set Variables** — Create n8n variables:
   - epoUrl — https://api.github.com/repos/owner/repo
   - githubToken — Your GitHub PAT with repo scope
   - claudeApiKey — Your Anthropic API key
   - webhookUrl — Slack/Discord webhook URL
   - language — EN or FR
3. **Activate** — Toggle the workflow to **Active** in n8n
4. **Test** — Click **Execute Workflow** to run a manual test
5. **Wait for Friday 5pm UTC** — Or adjust the cron in the trigger node

## Output

A Slack message with a narrative summary covering:
- Key highlights and major changes
- Bug fixes and improvements
- Notable patterns or trends
- Overall project health

## Requirements

- n8n v1.0+ (self-hosted or cloud)
- GitHub personal access token
- Anthropic API key (Claude Sonnet 4)
- Slack webhook (or edit the last node for Discord/email)
