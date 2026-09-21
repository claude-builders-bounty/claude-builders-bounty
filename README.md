# Weekly Dev Summary — n8n + Claude API Workflow

Automated weekly narrative summary of GitHub repository activity, generated via Claude API and delivered to Discord.

## Workflow

`weekly-dev-summary-workflow.json` — importable n8n workflow.

## Setup (5 Steps)

1. **Import** the workflow in n8n: *Workflows → Import → Select `weekly-dev-summary-workflow.json`*
2. **Configure credentials** in n8n environment variables or workflow parameters:
   - `GITHUB_TOKEN` — GitHub PAT with `repo` scope
   - `CLAUDE_API_KEY` — Anthropic API key for `claude-sonnet-4-20250514`
   - `DISCORD_WEBHOOK_URL` — Discord channel webhook URL
   - `GITHUB_REPO_OWNER` / `GITHUB_REPO_NAME` — target repository
   - `SUMMARY_LANGUAGE` — `EN` (default) or `FR`
3. **Activate** the workflow (toggle *Active* in n8n)
4. **Test** manually: click *Execute Workflow* to verify data fetch, summary generation, and Discord delivery
5. **Schedule** runs automatically every Friday at 17:00 Europe/Berlin (cron: `0 17 * * 5`)

## Delivery

- Primary: Discord webhook (configured via `DISCORD_WEBHOOK_URL`)
- Alternative: Email node included but disabled — enable `Send Email` node and set `FROM_EMAIL` / `TO_EMAIL` to use

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token with `repo` scope
- Anthropic API key with access to `claude-sonnet-4-20250514`
- Discord webhook URL (or SMTP for email)

## License

MIT