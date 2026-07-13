# n8n + Claude weekly development summary

This directory contains an importable n8n workflow that runs at 17:00 every
Friday, gathers the previous seven days of GitHub commits, closed issues, and
merged pull requests, asks Claude for an EN or FR narrative, and posts it to a
Slack incoming webhook.

## Configuration

The **Configuration** node keeps the values that are expected to change between
installations:

| Field | Required | Purpose |
| --- | --- | --- |
| `githubRepository` | Yes | Repository in `owner/name` form |
| `webhookUrl` | Yes | Slack incoming-webhook URL for the destination |
| `destinationChannel` | No | Channel label sent in the Slack payload; defaults to `#engineering` |
| `summaryLanguage` | No | `EN` or `FR`; any other value safely falls back to `EN` |

GitHub and Anthropic secrets use separate n8n **HTTP Header Auth** credentials,
so neither token is stored in the exported workflow. The workflow calls
`claude-sonnet-4-20250514`, is inactive when imported, and defaults to UTC.

## Setup in five steps

1. Import [`workflow.json`](./workflow.json) from **Workflows → Import from File**, or run `n8n import:workflow --input=workflow.json`.
2. Create two **HTTP Header Auth** credentials: GitHub with header `Authorization` and value `Bearer YOUR_TOKEN`, and Anthropic with header `x-api-key` and your Claude API key. Select the GitHub credential on all three **Fetch** nodes and the Anthropic credential on **Generate Narrative with Claude**.
3. Edit the four fields in **Configuration**, then open **Workflow settings** to change the UTC timezone if needed; confirm that **Every Friday at 5 PM** is configured for Friday at 17:00 (equivalent to cron `0 17 * * 5`).
4. Click **Execute workflow** once and verify the three GitHub requests, Claude response, and Slack delivery. Save a screenshot of the successful execution when submitting against issue #5.
5. Activate the workflow; n8n will now run it every Friday at 17:00 in the selected workflow timezone.

## What the workflow sends

The Slack request contains `channel` and `text`. The text includes the covered
UTC interval, Claude's narrative, and counts for commits, closed issues, and
merged pull requests. Modern Slack app webhooks are bound to the channel chosen
when the webhook is created; for those webhooks, use a URL for the desired
channel and keep `destinationChannel` as a matching label.

GitHub requests use the API maximum of 100 records per activity type. For a
repository that regularly exceeds that volume in seven days, add n8n HTTP
Request pagination before relying on the counts.

## Security notes

- Keep the GitHub and Anthropic tokens in n8n's encrypted credential store or
  external secret manager, and never commit them.
- Treat the Slack webhook URL as a secret. It lives in the Configuration node,
  so restrict workflow export and editor access.
- Give the GitHub token read-only access to only the repositories being
  summarized.
- Restrict workflow and execution-log access because API responses can contain
  repository metadata.
