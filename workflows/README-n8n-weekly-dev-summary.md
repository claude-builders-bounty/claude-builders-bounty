# n8n Weekly GitHub Activity Summary

Import `n8n-weekly-dev-summary.json` to run a weekly Friday 5pm workflow that fetches the last seven days of commits, closed issues, and merged pull requests from GitHub, asks Claude Sonnet 4 to write a narrative summary, and posts it to Discord.

## Setup

1. Import `workflows/n8n-weekly-dev-summary.json` in n8n.
2. Set environment variables: `GITHUB_REPO=owner/name`, `GITHUB_TOKEN=github_pat_or_token`, `ANTHROPIC_API_KEY=sk-ant-...`, `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...`, and optional `SUMMARY_LANGUAGE=EN` or `FR`.
3. Open the workflow and run `Manual Test Trigger` once to confirm GitHub, Claude, and Discord credentials work.
4. Check the Discord channel for the generated weekly summary.
5. Activate the workflow; it will run every Friday at 5pm using the n8n instance timezone.

## Notes

- `GITHUB_TOKEN` is optional for public repositories, but recommended to avoid low unauthenticated rate limits.
- The Claude model is fixed to `claude-sonnet-4-20250514` to match the bounty requirement.
- Discord messages are trimmed to stay under Discord's message size limit.
