# n8n Weekly Dev Summary

Importable n8n workflow that collects weekly GitHub activity, asks Claude for a narrative summary, and posts the result to Slack.

## Setup

1. Import `weekly-dev-summary.json` into n8n.
2. Create credentials for GitHub bearer auth, Anthropic API key, and Slack incoming webhook.
3. Edit the `Config` node values: `owner`, `repo`, `language`, and `slackWebhookUrl`.
4. Run the workflow manually once and verify the Slack message.
5. Activate the workflow; it runs every Friday at 17:00.

## Configurable Variables

- `owner`: GitHub repository owner.
- `repo`: GitHub repository name.
- `language`: `EN` or `FR`.
- `slackWebhookUrl`: destination Slack incoming webhook.

## What It Fetches

- commits from the last seven days
- issues closed in the last seven days
- pull requests merged in the last seven days

## Claude Model

The workflow calls Anthropic Messages API with `claude-sonnet-4-20250514` and asks for a concise weekly narrative summary.

## Validation

`weekly-dev-summary.json` is valid JSON and uses n8n export structure with nodes and connections. A live execution requires real GitHub, Anthropic, and Slack credentials, so the PR submitter should run the final manual execution inside their n8n instance before activation.
