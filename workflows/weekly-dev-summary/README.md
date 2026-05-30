# Weekly Dev Summary n8n Workflow

This workflow generates a weekly narrative summary for a GitHub repository using Claude and sends it to a Discord webhook.

## Setup

1. Import `weekly-dev-summary.n8n.json` into n8n.
2. Open the `Set Config` node and set `githubRepo`, `language`, `anthropicApiKey`, and `deliveryWebhookUrl`.
3. Keep `anthropicApiUrl` as `https://api.anthropic.com/v1/messages` unless you are running a local mock test.
4. Save and activate the workflow so the Friday 17:00 schedule can run automatically.
5. Run the workflow once manually to confirm the Discord message is delivered.

## Configuration

| Field | Example | Notes |
| --- | --- | --- |
| `githubRepo` | `n8n-io/n8n` | Repository in `owner/name` format. |
| `language` | `EN` | Supports `EN` or `FR`. |
| `anthropicApiKey` | `sk-ant-...` | Anthropic API key for Claude. |
| `anthropicApiUrl` | `https://api.anthropic.com/v1/messages` | Override only for local mock testing. |
| `deliveryWebhookUrl` | `https://discord.com/api/webhooks/...` | Discord webhook URL. |
| `maxItems` | `25` | Maximum commits, issues, and pull requests sent to Claude. |

## What It Does

- Runs every Friday at 17:00 using n8n's Schedule Trigger.
- Reads the last seven days of commits, closed issues, and merged pull requests from the GitHub API.
- Builds a concise prompt and calls Anthropic's Messages API with `claude-sonnet-4-20250514`.
- Sends the resulting narrative summary to Discord.

## Test Evidence

For the bounty PR, attach a screenshot of a successful n8n execution showing:

- `Fetch Commits`, `Fetch Closed Issues`, and `Fetch Closed Pull Requests` completed.
- `Generate Claude Summary` completed.
- `Send Discord Summary` completed.

