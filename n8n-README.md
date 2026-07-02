# n8n Weekly Dev Summary Workflow

Automatically generate a weekly development summary using n8n + Claude API.

## Features

- Weekly cron trigger (Fridays at 5pm)
- Fetches commits, merged PRs, and closed issues from GitHub
- Generates narrative summary via Claude API
- Delivers to Discord/Slack webhook

## Setup (5 Steps)

1. **Install n8n:** `npx n8n`
2. **Import workflow:** Settings → Workflows → Import from File → Select `weekly-summary.json`
3. **Add credentials:**
   - GitHub: Personal Access Token
   - Claude: API Key from https://console.anthropic.com
   - Webhook: Discord/Slack incoming webhook URL
4. **Configure variables:** Set repo owner/name, language (EN/FR), webhook URL
5. **Activate:** Toggle the workflow active

## Configuration

| Variable | Location | Description |
|----------|----------|-------------|
| GitHub repo | Fetch node URL | `owner/repo` format |
| Language | Claude API node | `EN` or `FR` |
| Webhook URL | Output node | Discord/Slack webhook |
