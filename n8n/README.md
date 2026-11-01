# Weekly Dev Summary (n8n + Claude)

An importable n8n workflow that generates a weekly narrative summary of a
GitHub repo's activity (commits, merged PRs, closed issues) using the
Claude API, and delivers it to a Slack/Discord webhook.

## Setup (5 steps)

1. In n8n: **Workflows → Import from File** → select `n8n/weekly-dev-summary.json`.
2. Set environment variables in your n8n instance:
   - `GITHUB_REPO` (e.g. `owner/repo`)
   - `ANTHROPIC_API_KEY`
   - `SLACK_WEBHOOK_URL` (Slack incoming webhook or Discord webhook URL)
   - `SUMMARY_LANGUAGE` (optional: `EN` or `FR`, default `EN`)
3. (GitHub) The workflow calls the public GitHub API; for private repos or
   higher rate limits set `GITHUB_TOKEN` and add an `Authorization: Bearer`
   header to the three GitHub HTTP nodes.
4. Activate the workflow. It runs every Friday at 17:00.
5. Wait for the first run (or execute manually) and check your channel.

## Node overview

`Cron (Fri 17:00)` → `Config` → `Compute week window` →
`Fetch commits` / `Fetch merged PRs` / `Fetch closed issues` →
`Aggregate activity` → `Claude API (claude-sonnet-4-20250514)` →
`Extract summary text` → `Deliver (Slack/Discord webhook)`.

## Notes

- The Claude prompt requests 8–12 sentences grouped by theme, in the
  configured language.
- If `SLACK_WEBHOOK_URL` is empty the delivery node will fail; that is
  intentional — configure a destination before activating.
- Tested structurally (valid JSON, all nodes connected) but not executed on
  a live n8n instance in this repo. Please report any tweaks needed for your
  n8n version.

MIT License.
