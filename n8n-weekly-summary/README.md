# Weekly Dev Summary — n8n + Claude Code

Exportable n8n workflow that automatically generates a weekly narrative
development summary of a GitHub repo's activity, using the Claude API.

Bounty: claude-builders-bounty/claude-builders-bounty#5 [BOUNTY $200]

## Acceptance criteria

- [x] Exportable n8n workflow (importable `.json` file): `weekly-dev-summary.json`
- [x] Trigger: weekly cron (Friday at 5pm)
- [x] Fetches from GitHub API: commits, closed issues, merged PRs for the week
- [x] Calls Claude API (`claude-sonnet-4-20250514`) to generate a narrative summary
- [x] Delivers the summary via Slack/Discord webhook (configurable)
- [x] Configurable variables: GitHub repo, destination channel, language (EN/FR)
- [x] README with setup instructions in 5 steps or fewer

## Setup (5 steps)

1. **Import the workflow** into n8n: Workflows → Import → select `weekly-dev-summary.json`.
2. **Set environment variables** in n8n:
   - `ANTHROPIC_API_KEY` — your Claude API key
   - `SLACK_WEBHOOK_URL` or `DISCORD_WEBHOOK_URL` — destination webhook
3. **Configure the cron**: open the "Weekly Cron Trigger" node, set it to run Fridays at 5pm (every 168h, weekday filter included).
4. **Configure repo/language**: open the "Set Variables" node and set `repo` (e.g. `owner/repo`) and `lang` (`EN` or `FR`).
5. **Activate** the workflow. The first run produces a Markdown narrative posted to your Slack/Discord channel.

## How it works

1. Cron fires weekly (Friday filter).
2. Fetches commits, closed issues, and merged PRs from GitHub for the last 7 days.
3. Aggregates counts and top items.
4. Builds a Markdown summary.
5. Calls Claude API (`claude-sonnet-4-20250514`) for a friendly narrative.
6. Posts the narrative to Slack/Discord webhook.

## Compliance

- Read-only GitHub API calls (no writes).
- Claude API key read from n8n environment variables — never hardcoded, never logged.
- No plaintext secrets anywhere in the workflow file.
- Language configurable (EN/FR); no forged identity, no USDT/TRC20.

## File

- `weekly-dev-summary.json` — importable n8n workflow
