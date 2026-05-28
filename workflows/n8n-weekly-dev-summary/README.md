# n8n Weekly Dev Summary

This workflow generates a weekly narrative summary of GitHub repository activity with Claude and sends it to Slack, Discord, or email.

## Setup

1. Import `workflows/n8n-weekly-dev-summary.json` into n8n.
2. Set environment variables: `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `SUMMARY_LANGUAGE=EN` or `FR`, and `DELIVERY_MODE=slack` or `email`.
3. For Slack or Discord, set `DESTINATION_WEBHOOK_URL`; for email, configure n8n SMTP credentials and set `DESTINATION_EMAIL`.
4. Open the workflow, run `Manual test trigger`, and inspect the generated summary.
5. Activate the workflow to run every Friday at 5pm.

## What It Fetches

- Commits from the last seven days.
- Issues closed since the start of the weekly window.
- Pull requests merged since the start of the weekly window.

## Claude Request

The workflow calls Anthropic Messages API with:

```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 900
}
```

The prompt asks Claude to produce a narrative weekly development summary in English or French using only the fetched GitHub activity.

## Delivery

- `DELIVERY_MODE=slack`: sends `{ "text": "..." }` to `DESTINATION_WEBHOOK_URL`. Discord webhooks accept the same payload shape for simple messages.
- `DELIVERY_MODE=email`: sends the summary through n8n's Email Send node to `DESTINATION_EMAIL`.

## Validation

The workflow JSON is covered by `tests/test_n8n_weekly_summary_workflow.py`, which verifies that the importable file includes the weekly trigger, GitHub fetch nodes, Claude API call, delivery nodes, configurable variables, and required model name.

Manual n8n execution still requires real `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, and destination credentials.
