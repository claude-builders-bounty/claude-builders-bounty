# Weekly Dev Summary — n8n + Claude ($200 bounty #5)

An n8n workflow that automatically generates a weekly narrative summary of a
GitHub repo's activity using the Claude API, delivered to Discord.

## What it does

1. **Trigger**: every Friday at 5pm (`cron` node, expression `0 17 * * FRI`)
2. **Fetch** from GitHub API (last 7 days):
   - Commits (`/repos/{repo}/commits?since=...`)
   - Closed issues (`/repos/{repo}/issues?state=closed`)
   - Closed/merged PRs (`/repos/{repo}/pulls?state=closed`)
3. **Aggregate** into a compact text blob (function node)
4. **Call Claude API** (`claude-sonnet-4-20250514`) to write a 2–4 paragraph narrative
5. **Deliver** to Discord via webhook (embed with summary)

## Setup (5 steps)

1. Import `workflow.json` into n8n (Menu → Import from File).
2. Create credentials:
   - **GitHub Token** (httpHeaderAuth): header `Authorization: Bearer ghp_xxx`
   - **Anthropic API Key** (httpHeaderAuth): header `x-api-key: sk-ant-xxx`
3. Set n8n environment variables (or edit node expressions):
   - `GITHUB_REPO` — e.g. `owner/repo`
   - `DISCORD_WEBHOOK` — your Discord channel webhook URL
   - `LANGUAGE` — `EN` or `FR`
4. (Optional) Test immediately: click **Execute Workflow** (cron will be skipped).
5. Activate the workflow (toggle top-right).

## Configurable variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | — | owner/repo to summarize |
| `DISCORD_WEBHOOK` | — | destination channel |
| `LANGUAGE` | EN | summary language (EN/FR) |

## Notes

- GitHub API uses `since` = now − 7 days to bound the weekly window.
- Claude prompt is templated with the aggregated commit/PR/issue lists.
- Discord delivery uses an embed; swap the `Discord Webhook` node for an
  Email/Slack node if preferred (both documented in n8n docs).
- The workflow is exported as `workflow.json` — importable on any n8n instance
  (self-hosted or cloud).
