# Weekly GitHub Dev Summary (n8n + Claude)

Automated Friday 5pm workflow: fetches commits, closed issues, and merged PRs from GitHub, asks Claude (`claude-sonnet-4-20250514`) for a narrative summary, posts to Discord.

## Setup (5 steps)

1. **Import** — In n8n: *Workflows → Import from File* → select `weekly-dev-summary.json`.
2. **Env vars** — Set `GITHUB_TOKEN` (repo read scope) and `ANTHROPIC_API_KEY` in n8n environment / host.
3. **GitHub auth** — Create Header Auth credential: name `Authorization`, value `Bearer <your_github_token>`. Attach it to nodes **Commits**, **Issues**, **PRs**.
4. **Config node** — Edit **Config**: set `githubRepo` (`owner/name`), `language` (`EN` or `FR`), `discordWebhook` (channel webhook URL).
5. **Activate** — Save, toggle Active. Optional: *Execute Workflow* once to verify; check Discord for the summary.

## Delivery

**Discord webhook** (default). Create one in Server Settings → Integrations → Webhooks.

## Notes

- Cron: `0 17 * * 5` (Friday 17:00 server time).
- Window: last 7 days (`since` ISO date).
- Swap Discord for Slack by changing the final HTTP node URL/body to a Slack incoming webhook.
