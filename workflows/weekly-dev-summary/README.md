# Weekly Dev Summary: n8n + Claude

An importable n8n workflow that pulls a week's worth of GitHub activity, turns it into a clean context block, asks Claude for a narrative summary, and delivers the result by email and/or Slack webhook.

## Setup in 5 Steps

1. Import `weekly-dev-summary.json` into n8n.
2. Add a **GitHub Token** credential using HTTP Header Auth:
   - header: `Authorization`
   - value: `Bearer <your-github-token>`
3. Add an **Anthropic API Key** credential using HTTP Header Auth:
   - header: `x-api-key`
   - value: `<your-anthropic-api-key>`
4. Configure environment variables:
   - `GITHUB_REPO=owner/repo`
   - `LANGUAGE=EN` or `FR`
   - `SLACK_WEBHOOK_URL=https://hooks.slack.com/...` (optional)
   - `SMTP_FROM=dev@example.com` and `EMAIL_TO=team@example.com` (optional)
5. Activate the workflow. It runs every Friday at 5 PM.

## Workflow Shape

```text
Friday 5 PM
  -> Fetch commits
  -> Fetch closed issues
  -> Fetch closed PRs
  -> Build weekly context
  -> Ask Claude for a narrative summary
  -> Format Markdown
  -> Send Email and/or Post to Slack
```

## What It Produces

The generated summary stays under 400 words and includes:

1. a short weekly overview,
2. key highlights,
3. notable merged changes, and
4. notable closed issues.

## Why This Version Is Safer

- filters out pull requests from the issues feed,
- filters PRs by `merged_at` inside the last week instead of relying on `updated_at`,
- calls Anthropic directly via HTTP instead of pretending Anthropic is OpenAI-compatible, and
- keeps delivery optional so email and Slack can be enabled independently.

## Delivery Notes

- Slack uses the `text` field out of the box.
- To switch to Discord, duplicate the webhook node and send `content` instead of `text`.
- If you only want one destination, disable or delete the other output node.

## Validation Notes

The workflow is designed to be tested against a real n8n instance by:

1. manually executing the schedule trigger,
2. checking that the GitHub nodes return the last 7 days of activity,
3. confirming Claude returns a readable narrative, and
4. verifying the message lands in Slack or email.
