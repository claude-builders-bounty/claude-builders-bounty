# Weekly GitHub Dev Summary (n8n + Claude)

Importable n8n workflow: every **Friday 17:00**, fetch last 7 days of GitHub activity, summarize with **Claude Sonnet 4**, deliver to **Discord**.

## Setup (5 steps)

1. Import [`workflow.json`](./workflow.json) in n8n (**Workflows → Import from File**).
2. Set environment variables in n8n (Settings → Variables) or your process manager:
   - `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_TOKEN`
   - `ANTHROPIC_API_KEY`
   - `DISCORD_WEBHOOK_URL`
   - `SUMMARY_LANGUAGE` (`EN` or `FR`)
3. Activate the workflow and click **Execute Workflow** once to validate credentials.
4. Confirm Discord receives a narrative summary with sections (Highlights / Shipped / Fixes / etc.).
5. Leave the cron trigger enabled for weekly runs.

## What it fetches

- Commits since 7 days ago (`/commits?since=...`)
- Closed issues (`/issues?state=closed&since=...`, PRs filtered out)
- Merged pull requests (`/pulls?state=closed`, `merged_at` present)

## Model

Uses Anthropic **`claude-sonnet-4-20250514`** via `POST /v1/messages`.

## Manual test without waiting for Friday

Open the workflow → **Execute Workflow**. The schedule trigger is bypassed when executing manually from the editor.

## Screenshot

After a successful manual execution, capture the n8n execution panel showing green nodes and the Discord delivery step. Attach that screenshot to the bounty PR.
