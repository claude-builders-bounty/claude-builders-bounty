# n8n Weekly Dev Summary Workflow

This importable n8n workflow generates a weekly narrative summary of a GitHub repository using the Claude API, then posts the result to a Slack or Discord-compatible webhook.

## Setup in 5 steps

1. Import `workflow.json` into n8n.
2. Add GitHub credentials to the GitHub nodes.
3. Add an HTTP Header Auth credential for Anthropic with `x-api-key: <ANTHROPIC_API_KEY>`.
4. Edit the `Config` node: `github_owner`, `github_repo`, `language` (`EN` or `FR`), and `destination_webhook`.
5. Run once manually, confirm the webhook receives the summary, then activate the weekly Friday 5 PM trigger.

## What it does

- Runs every Friday at 5 PM.
- Fetches GitHub commits from the last 7 days.
- Fetches closed issues from the last 7 days.
- Fetches closed/merged pull requests.
- Calls Claude API with `claude-sonnet-4-20250514`.
- Sends the narrative summary to the configured webhook.

## Configurable variables

| Variable | Purpose |
| --- | --- |
| `github_owner` | GitHub repository owner |
| `github_repo` | GitHub repository name |
| `language` | Summary language, e.g. `EN` or `FR` |
| `destination_webhook` | Slack/Discord-compatible webhook URL |

## Validation

The JSON export was validated with:

```bash
python3 -m json.tool workflows/n8n-weekly-summary/workflow.json
```

Manual n8n validation checklist:

- Import succeeds without JSON errors.
- GitHub nodes return commits, closed issues, and pull requests.
- Claude API node returns a text summary.
- Final webhook receives the generated message.

## Successful execution evidence

After importing into n8n, run the workflow manually and attach a screenshot showing the green execution path from `Weekly Schedule` through `Send Webhook`.
