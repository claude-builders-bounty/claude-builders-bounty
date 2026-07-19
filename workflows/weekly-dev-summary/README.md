# Weekly Dev Summary (n8n + Claude)

Importable n8n workflow that posts a weekly narrative of a GitHub repo's activity to Discord.

Built for the Opire [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) ($200).

## Setup (5 steps)

1. **Import** `weekly-dev-summary.workflow.json` into n8n (Workflows → Import from File).
2. **Set env vars** on the n8n instance (or edit the Config node defaults):
   - `GITHUB_OWNER` / `GITHUB_REPO` — target repository
   - `GITHUB_TOKEN` — GitHub PAT with `repo` or public `public_repo` read
   - `ANTHROPIC_API_KEY` — Claude API key
   - `DISCORD_WEBHOOK_URL` — Discord channel webhook
   - `SUMMARY_LANG` — `EN` or `FR`
3. **Activate** the workflow (cron: Friday 17:00 — change timezone in Schedule node if needed).
4. **Test** with "Execute Workflow" (or temporarily switch the Schedule node to Manual Trigger).
5. **Confirm** Discord receives the weekly summary.

## What it does

- Weekly cron (Friday 5pm)
- Fetches commits, closed issues, and merged PRs for the last 7 days via GitHub API
- Calls Claude (`claude-sonnet-4-20250514`) for a narrative summary
- Delivers via Discord webhook

## Delivery choice

Discord webhook (documented). Swap the final HTTP Request node for Slack Incoming Webhook or Gmail if preferred.

## Test evidence

See `docs/execution-proof.md` and `docs/sample-summary.md` for a dry-run against a real public repo (same data path the workflow uses).

## License

MIT
