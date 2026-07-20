# n8n weekly GitHub summary workflow ($200)

Importable n8n workflow: weekly cron → GitHub API activity → Claude narrative → Discord webhook.

## Setup (5 steps)

1. Import `workflow.json` into n8n (**Workflows → Import**).
2. Set credentials:
   - **GitHub** personal access token (classic: `repo` or public `public_repo`)
   - **Anthropic** API key
   - **Discord** webhook URL (or swap the last node for email/Slack)
3. Edit workflow variables (or Set node):
   - `GITHUB_OWNER`, `GITHUB_REPO`
   - `LANGUAGE` = `EN` or `FR`
   - `DISCORD_WEBHOOK_URL`
4. Activate the workflow (cron: Friday 17:00).
5. Click **Test workflow** once; confirm Discord message arrives.

## What it does

1. Cron trigger (weekly Friday 5pm).
2. Fetches last 7 days: commits, closed issues, merged PRs via GitHub REST.
3. Builds a compact activity blob.
4. Calls Claude (`claude-sonnet-4-20250514`) for a narrative summary in EN/FR.
5. Posts to Discord webhook.

## Files

- `workflow.json` — n8n export
- `sample-output.md` — example narrative (from public repo activity shape)

## Author

@cornerblue — BTC `bc1qjtevjy8gldfhkra6n5g4yclpr5uafyd7k0j2ls`
