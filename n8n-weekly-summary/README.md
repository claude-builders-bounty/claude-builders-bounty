# n8n Weekly Dev Summary Workflow

Automatically generates a narrative weekly summary of a GitHub repository's activity using the Claude API, delivered via Discord or Slack webhook.

## Acceptance Criteria Met
- [x] Exportable n8n workflow (`weekly-dev-summary.json`)
- [x] Weekly cron trigger (Friday 5pm UTC)
- [x] Fetches commits, closed issues, merged PRs from GitHub API
- [x] Calls Claude API (`claude-sonnet-4-20250514`) for narrative summary
- [x] Delivers via Discord/Slack webhook
- [x] Configurable: GitHub repo, webhook URL, language (EN/FR)
- [x] README with setup in 5 steps

## Setup (5 Steps)

1. **Import workflow** — In n8n: Workflows → Import → select `weekly-dev-summary.json`
2. **Add GitHub credentials** — Credentials → New → HTTP Header Auth → name `githubApi` → header `Authorization: Bearer <GH_TOKEN>`
3. **Add Claude API credentials** — Credentials → New → HTTP Header Auth → name `claudeApi` → header `x-api-key: <ANTHROPIC_KEY>`
3. **Configure parameters** — Open workflow → click "Parameters" → set:
   - `githubRepo`: your repo (e.g., `facebook/react`)
   - `webhookUrl`: Discord/Slack incoming webhook URL
   - `language`: `EN` or `FR`
4. **Activate** — Toggle workflow active. Runs every Friday 5pm UTC.

## Test Run

Click **Execute Workflow** in n8n editor. Check Discord/Slack for the summary message.

## Screenshot

![Workflow execution](screenshot.png)

*(Add a real screenshot after testing on your n8n instance)*
