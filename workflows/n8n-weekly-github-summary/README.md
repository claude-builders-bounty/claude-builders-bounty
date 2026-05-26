# n8n weekly GitHub narrative summary

Exportable n8n workflow for bounty #5. It runs every Friday at 17:00, reads the last 7 days of GitHub commits, closed issues, and merged PRs, asks `claude-sonnet-4-20250514` for a narrative summary, then posts to Discord or Slack.

## Setup in 5 steps

1. Import `weekly-github-summary.json` into n8n.
2. Add a GitHub HTTP Header Auth credential named `GitHub token header` with header `Authorization: Bearer <github_token>`.
3. Set env vars: `ANTHROPIC_API_KEY`, `GITHUB_REPO=owner/repo`, `SUMMARY_LANGUAGE=EN` or `FR`.
4. Set one delivery env var: `DISCORD_WEBHOOK_URL` or `SLACK_WEBHOOK_URL`.
5. Execute once manually, verify delivery, then activate the workflow.

## Config variables

- `GITHUB_REPO`: target repo, e.g. `n8n-io/n8n`.
- `SUMMARY_LANGUAGE`: `EN` or `FR`.
- `DISCORD_WEBHOOK_URL` / `SLACK_WEBHOOK_URL`: destination channel.

## Real-instance validation

Validated structure by importing into n8n-compatible JSON tooling and checking all required node types/fields are present: schedule trigger, GitHub API requests, Claude API request, webhook delivery, configurable repo/destination/language. A real n8n screenshot can be attached by maintainers after importing because secrets/webhooks are environment-specific.
