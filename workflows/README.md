# n8n Weekly Dev Summary

This directory contains an importable n8n workflow that posts a weekly GitHub development summary to Discord. It runs every Friday at 5pm, fetches commits, closed issues, and merged pull requests from the GitHub API for the previous seven days, then asks Claude `claude-sonnet-4-20250514` to write the narrative summary.

## Setup

1. Import `workflows/n8n-weekly-dev-summary.json` into n8n.
2. Set these n8n environment variables: `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, and optional `SUMMARY_LANGUAGE=EN` or `SUMMARY_LANGUAGE=FR`.
3. Open the imported workflow and confirm the "Weekly Friday 5pm Trigger" node matches your timezone requirements.
4. Execute the workflow once manually to verify GitHub, Claude, and Discord connectivity.
5. Activate the workflow.

## Delivery

The workflow delivers summaries through a Discord incoming webhook. Use the webhook URL as `DISCORD_WEBHOOK_URL`; no Discord credentials are stored in the workflow file.

## Configuration

- `GITHUB_REPO`: target repository in `owner/repo` format.
- `DISCORD_WEBHOOK_URL`: destination channel webhook.
- `SUMMARY_LANGUAGE`: `EN` for English or `FR` for French.
- `GITHUB_TOKEN`: token with read access to the repository.
- `ANTHROPIC_API_KEY`: key used for the Claude Messages API call.

## Validation

The workflow JSON is exportable/importable n8n JSON and can be syntax-checked locally with:

```bash
jq empty workflows/n8n-weekly-dev-summary.json
```

The bounty acceptance criteria request a screenshot from a real n8n execution. That screenshot must be captured from the target n8n instance after importing and running the workflow because this repository does not include an n8n runtime or credentials.
