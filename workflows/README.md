# Weekly GitHub Dev Summary Workflow

This n8n workflow generates a weekly narrative summary of a GitHub repository with Claude and posts it to a Slack-compatible or Discord-compatible webhook.

## Setup

1. Import `n8n-weekly-dev-summary.json` into n8n.
2. Set environment variables: `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DESTINATION_WEBHOOK_URL`, and `SUMMARY_LANGUAGE=EN` or `FR`.
3. Open the workflow and confirm the schedule is Friday at 5pm.
4. Run the workflow manually once and confirm the webhook receives the summary.
5. Activate the workflow.

## What It Does

- Triggers weekly on Friday at 5pm.
- Fetches commits, closed issues, and merged PRs from the GitHub API for the last 7 days.
- Calls the Claude Messages API with `claude-sonnet-4-20250514`.
- Sends the generated narrative summary to a Slack-compatible or Discord-compatible webhook.

## Configurable Variables

| Variable | Required | Example | Description |
|---|---:|---|---|
| `GITHUB_REPO` | Yes | `n8n-io/n8n` | Repository in `owner/repo` format. |
| `GITHUB_TOKEN` | Recommended | `github_pat_...` | Raises GitHub API rate limits and allows private repos. |
| `ANTHROPIC_API_KEY` | Yes | `sk-ant-...` | Claude API key. |
| `DESTINATION_WEBHOOK_URL` | Yes | `https://discord.com/api/webhooks/...` | Destination Slack or Discord webhook. |
| `SUMMARY_LANGUAGE` | No | `EN` or `FR` | Summary language. Defaults to `EN`. |

## Verification

Run the JSON validator before importing:

```bash
python3 workflows/validate_workflow.py
```

The bounty asks for a screenshot from a real n8n execution. After importing and running the workflow, attach a screenshot showing the successful execution and webhook delivery to the pull request.
