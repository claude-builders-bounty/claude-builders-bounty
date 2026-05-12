# n8n Weekly Dev Summary Workflow

Import `workflow.json` into n8n to post a weekly repository summary generated from GitHub activity and Claude.

## What it does

- Runs every Friday at 17:00 (`America/New_York`) via Cron.
- Collects last-7-day commits, closed issues, and merged PRs from one GitHub repository.
- Asks Claude to generate a concise weekly summary.
- Sends the summary to a configurable webhook destination channel.
- Supports output language in English (`EN`) or French (`FR`).

## Required variables

Configure these in n8n environment variables (or replace expressions in `Set Run Config`):

- `GITHUB_REPO_OWNER` (example: `owner`)
- `GITHUB_REPO_NAME` (example: `repo`)
- `DESTINATION_WEBHOOK_URL` (Slack/Discord/custom webhook)
- `DESTINATION_CHANNEL` (channel label for summary context)
- `SUMMARY_LANGUAGE` (`EN` or `FR`)
- `GITHUB_TOKEN` (token with repo-read scope)
- `CLAUDE_API_KEY`
- `CLAUDE_MODEL` (optional, default `claude-3-5-sonnet-latest`)

## Setup (5 steps)

1. Import `workflow.json` into n8n.
2. Set the environment variables above and verify the destination webhook accepts JSON `{ "text": "..." }`.
3. Open **Set Run Config** and confirm repo/channel/language defaults are correct.
4. Click **Test workflow** and verify **Send Summary To Webhook** returns `2xx`.
5. Capture an execution screenshot and store it in `evidence/successful-execution.png`, then activate the workflow.

## Notes

- The closed-issues step filters out pull requests and keeps only issues closed in the past week.
- The merged-PR step filters by `merged_at` within the same 7-day window.
- If Claude returns no text, the workflow emits a fallback message so failures are visible.
