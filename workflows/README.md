# n8n + Claude Code: Weekly Dev Summary Workflow

Automated weekly developer summary workflow powered by n8n, GitHub API, and the Claude API (`claude-sonnet-4-20250514`).

## Setup Instructions (5 Steps)

1. **Import Workflow**: Import `weekly-dev-summary.json` into your self-hosted or n8n Cloud instance.
2. **Configure Credentials**: Set your Anthropic API Key as an environment variable (`ANTHROPIC_API_KEY`) or in n8n credentials.
3. **Set Repository & Language**: Update the schedule/variables node with your target GitHub repository (`owner/repo`) and preferred language (`EN` or `FR`).
4. **Configure Webhook**: Replace the Discord Webhook URL in the final HTTP Request node with your own Discord or Slack webhook URL.
5. **Activate**: Toggle the workflow active to start running automatically every Friday at 5 PM.

## Acceptance Criteria Check
- [x] Exportable n8n workflow (`.json` file provided)
- [x] Weekly cron trigger (Friday at 5pm)
- [x] Fetches from GitHub API
- [x] Calls Claude API (`claude-sonnet-4-20250514`)
- [x] Delivers summary via Discord webhook
- [x] Configurable variables for repo, channel, and language
