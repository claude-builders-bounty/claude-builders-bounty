# Weekly GitHub Dev Summary with Claude + n8n

This workflow generates a weekly narrative summary of a GitHub repository using Claude and delivers it to a Slack or Discord webhook.

## Setup in 5 steps

1. Import `workflows/weekly-dev-summary-claude.json` into n8n.
2. Add a GitHub credential to the three GitHub HTTP Request nodes.
3. Set environment variables: `GITHUB_REPO=owner/repo`, `ANTHROPIC_API_KEY=...`, `DESTINATION_WEBHOOK_URL=...`, `SUMMARY_LANGUAGE=EN` or `FR`.
4. Run the workflow manually once and confirm the webhook receives a summary.
5. Activate the workflow; it runs every Friday at 17:00.

## What it fetches

- Commits from the last 7 days.
- Issues closed since the weekly window start.
- Pull requests merged since the weekly window start.

## Claude prompt behavior

The prompt asks `claude-sonnet-4-20250514` for a concise narrative summary with:

- shipped work
- closed issues
- merged PRs
- notable risks
- suggested next-week focus

## Configurable variables

| Variable | Example | Purpose |
|---|---|---|
| `GITHUB_REPO` | `owner/repo` | Repository to summarize |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Claude API key |
| `DESTINATION_WEBHOOK_URL` | Slack/Discord webhook | Delivery target |
| `SUMMARY_LANGUAGE` | `EN` or `FR` | Output language |

## Validation notes

The workflow JSON was parsed with Python's `json` module and inspected for the required nodes: weekly trigger, GitHub fetches, Claude call, configurable prompt, and webhook delivery.

Because this repository does not include a live n8n instance or real webhook credentials, `sample_outputs/manual_test_summary.md` documents the manual test shape and expected output using the same payload fields.
