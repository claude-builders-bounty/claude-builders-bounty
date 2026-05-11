# n8n Weekly GitHub Dev Summary with Claude

Importable n8n workflow that runs every Friday at 5pm, fetches a GitHub repo's weekly commits, closed issues, and merged PRs, asks Claude to write a narrative summary, and posts it to Discord.

## Setup in 5 steps

1. Import `weekly-dev-summary.workflow.json` into n8n.
2. Set environment variables: `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, and optional `SUMMARY_LANGUAGE` (`EN` or `FR`).
3. Open the workflow and confirm the Friday 5pm schedule fits your timezone.
4. Run the workflow manually once to verify GitHub, Claude, and Discord credentials.
5. Activate the workflow.

## Configurable variables

- `GITHUB_OWNER` — GitHub org/user, e.g. `openai`
- `GITHUB_REPO` — repo name, e.g. `openai-node`
- `GITHUB_TOKEN` — GitHub token with public repo read access, or private repo access if needed
- `ANTHROPIC_API_KEY` — Claude API key
- `DISCORD_WEBHOOK_URL` — destination Discord webhook
- `SUMMARY_LANGUAGE` — `EN` or `FR`; defaults to `EN`

## Claude model

The workflow calls `claude-sonnet-4-20250514` via the Anthropic Messages API.

## Delivery

Discord webhook. Swap the final HTTP Request node for Slack/email if preferred.

## Test status

The workflow JSON is syntactically valid and designed for n8n import. A real n8n execution screenshot is not included in this repository because this submission was prepared from a local CLI environment without browser access to a running n8n instance.
