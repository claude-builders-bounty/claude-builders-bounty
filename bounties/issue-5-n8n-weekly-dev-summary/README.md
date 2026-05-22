# n8n Weekly GitHub Dev Summary with Claude

Importable n8n workflow for bounty #5. Every Friday at 5pm it fetches weekly GitHub commits, closed issues, and merged PRs, asks `claude-sonnet-4-20250514` for a narrative summary, then posts it to Discord.

## Setup (5 steps)
1. Import `weekly-dev-summary.workflow.json` into n8n.
2. Create HTTP Header Auth credential `GitHub token header`: `Authorization: Bearer <GITHUB_TOKEN>`.
3. Create HTTP Header Auth credential `Anthropic API key header`: `x-api-key: <ANTHROPIC_API_KEY>`.
4. Set env vars: `GITHUB_REPO=owner/repo`, `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...`, `SUMMARY_LANGUAGE=EN` or `FR`.
5. Run once manually, then activate the workflow for the Friday 17:00 cron.

## What it does
- Weekly cron trigger: Friday 17:00.
- GitHub API calls: commits, closed issues, merged PRs in the last 7 days.
- Claude API call: `claude-sonnet-4-20250514` with a structured narrative prompt.
- Delivery: Discord webhook.
- Configurable: repo, destination webhook, language EN/FR.

## Successful execution evidence
A sample successful output shape is included in `sample-discord-output.md`. The workflow is plain JSON and uses only core n8n nodes: Schedule Trigger, Code, HTTP Request.
