# n8n + Claude Weekly Development Summary

This workflow generates a weekly narrative summary of a GitHub repository's activity with Claude and posts it to Slack.

## Setup in 5 steps

1. Import `workflows/weekly-dev-summary-n8n.json` into n8n.
2. Set these n8n environment variables or replace the values in the **Config** node:
   - `GITHUB_REPO` — repository slug, for example `owner/repo`
   - `GITHUB_TOKEN` — optional GitHub token for higher rate limits/private repos
   - `ANTHROPIC_API_KEY` — Claude API key
   - `SLACK_WEBHOOK_URL` — destination Slack incoming webhook URL
   - `SUMMARY_LANGUAGE` — `EN` or `FR`
3. Open the workflow and run **Manual Trigger** once to verify the configuration.
4. Check the Slack destination for the generated summary.
5. Activate the workflow. The **Weekly Friday 5pm Trigger** runs every Friday at 17:00.

## What it does

- Computes a one-week reporting window.
- Fetches from the GitHub API:
  - commits for the week
  - closed issues updated during the week
  - merged pull requests updated during the week
- Calls Anthropic Messages API with `claude-sonnet-4-20250514`.
- Posts the generated narrative summary to Slack.

## Configurable variables

| Variable | Purpose | Example |
|---|---|---|
| `GITHUB_REPO` | GitHub repository to summarize | `n8n-io/n8n` |
| `GITHUB_TOKEN` | Optional GitHub token | `github_pat_...` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook destination | `https://hooks.slack.com/services/...` |
| `SUMMARY_LANGUAGE` | Output language | `EN` or `FR` |

## Validation performed for this PR

- JSON syntax validation with Python `json.load`.
- Static workflow inspection to verify required nodes exist:
  - weekly cron trigger
  - GitHub activity fetch code node
  - Claude API HTTP request node using `claude-sonnet-4-20250514`
  - Slack webhook delivery node
- Repeatable validator included at `tests/validate_weekly_dev_summary_workflow.py`:
  ```bash
  python tests/validate_weekly_dev_summary_workflow.py
  ```

A real n8n execution still requires live `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL` values in the target n8n instance.
