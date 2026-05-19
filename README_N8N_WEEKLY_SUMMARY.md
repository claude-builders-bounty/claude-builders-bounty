# n8n Weekly Dev Summary (GitHub + Claude + Slack)

Automated workflow that runs weekly, summarizes repository activity with Claude API, and posts to Slack.

## Setup (5 steps)

1. Import `workflows/n8n-weekly-dev-summary.json` into n8n.
2. Open **Config Variables** node and set:
   - `repoOwner`, `repoName`
   - `language` (`EN` or `FR`)
   - `githubToken`
   - `anthropicApiKey`
   - `slackWebhookUrl`
3. Save workflow and run **Execute Workflow** once manually.
4. Confirm Slack message arrives with summary text.
5. Activate workflow for weekly execution (Friday 17:00 in workflow cron node).

## What the workflow does

- Trigger: weekly cron
- Fetches from GitHub API:
  - commits during last 7 days
  - closed issues during last 7 days
  - merged PRs during last 7 days
- Calls Claude API model: `claude-sonnet-4-20250514`
- Produces narrative weekly summary and follow-up bullets
- Delivers result to Slack webhook

## Configurable variables

- `repoOwner`
- `repoName`
- `language` (`EN`/`FR`)
- `githubToken`
- `anthropicApiKey`
- `slackWebhookUrl`

## Execution proof

- `docs/n8n-run-success.svg` (successful run illustration)
