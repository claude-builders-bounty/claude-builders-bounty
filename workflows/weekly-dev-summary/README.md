# Weekly dev summary (n8n) — setup (≤5 steps)

1. Import `n8n-weekly-dev-summary.json` into n8n.
2. Set env: `GITHUB_REPO=owner/name`, `ANTHROPIC_API_KEY`, `WEBHOOK_URL` (Discord/Slack), optional `SUMMARY_LANG=EN|FR`.
3. Attach GitHub HTTP header auth credential to the commits node.
4. Enable the workflow (cron: Friday 17:00).
5. Execute once manually and confirm the webhook receives a narrative summary.

Model id in the Anthropic Messages node: `claude-sonnet-4-20250514`.
