# n8n Weekly Dev Summary

Automated weekly development summary for any GitHub repo, powered by n8n and Claude API.

## Setup (5 steps)

1. **Import the workflow** — In n8n, go to **Workflows → Import from File** and select `n8n-weekly-summary.json`.

2. **Add credentials**:
   - `githubApi` — GitHub personal access token with `repo` scope
   - `claudeApi` — Anthropic API key with access to `claude-sonnet-4-20250514`

3. **Configure variables** — Open the workflow and set the workflow-level parameters:
   - `repoOwner` / `repoName` — GitHub repository to summarize
   - `defaultBranch` — Branch to fetch commits from (default: `main`)
   - `language` — Summary language: `EN` or `FR`
   - `webhookUrl` — Discord webhook URL for delivery

4. **Activate** — Toggle the workflow to Active.

5. **Done** — The workflow runs every Friday at 5pm. You can also click **Execute Workflow** to test immediately.

## What It Does

| Step | Action |
|------|--------|
| Cron trigger | Runs weekly (Fri 5pm) |
| GitHub API | Fetches merged PRs, closed issues, and recent commits |
| Claude API | Generates a narrative summary from the data |
| Discord webhook | Delivers the formatted summary |

## Delivery

Currently configured for Discord webhook. To switch to Slack, replace `webhookUrl` with a Slack webhook URL and change the body format as needed.
