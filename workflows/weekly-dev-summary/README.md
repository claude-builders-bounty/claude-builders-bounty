# Weekly GitHub Dev Summary Workflow

This n8n workflow generates a weekly narrative summary for a GitHub repository using the Claude API, then posts the result to a Slack or Discord-compatible webhook.

## Setup

1. Import `weekly-dev-summary.n8n.json` into n8n.
2. Set environment variables: `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DESTINATION_WEBHOOK_URL`, and optional `SUMMARY_LANGUAGE` (`EN` or `FR`).
3. Open the workflow and confirm the schedule node is set to Friday at 5:00 PM in your n8n instance timezone.
4. Run the workflow manually once and verify the webhook receives the generated summary.
5. Activate the workflow.

## What It Fetches

- Commits from the last seven days.
- Closed GitHub issues updated since the start of the weekly window.
- Merged pull requests updated since the start of the weekly window.

The workflow compacts those records before calling Claude so the prompt stays focused and avoids sending unnecessary GitHub payload fields.

## Claude Prompt

The Claude API node uses `claude-sonnet-4-20250514` and asks for:

- A headline.
- Shipped work.
- Resolved issues.
- Notable contributors.
- Operational risk.
- Next-week focus.

`SUMMARY_LANGUAGE=FR` switches the generated summary to French. Any other value defaults to English.

## Delivery

The final node posts JSON to `DESTINATION_WEBHOOK_URL`:

```json
{
  "text": "Weekly dev summary for owner/repo...",
  "repo": "owner/repo",
  "since": "2026-05-11T17:00:00.000Z",
  "until": "2026-05-18T17:00:00.000Z",
  "summary": "..."
}
```

Slack incoming webhooks accept the `text` field directly. Discord webhooks can also display `content`; if your Discord endpoint requires that field, change `payload.text` to `payload.content` in the "Format Webhook Payload" node.

## Test Evidence

Import validation completed by parsing `weekly-dev-summary.n8n.json` as JSON and checking for the required nodes: weekly schedule, GitHub commit/issues/PR fetches, Claude API call, and webhook delivery.

To complete the live-run evidence requested by the bounty, add a screenshot at:

```text
workflows/weekly-dev-summary/successful-execution.png
```

The screenshot should show one successful manual n8n execution with all nodes green.
