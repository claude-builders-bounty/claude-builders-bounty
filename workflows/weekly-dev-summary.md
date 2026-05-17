# Weekly Dev Summary Workflow

## Setup

1. Import `workflows/weekly-dev-summary.n8n.json` into n8n.
2. Set `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, and `SLACK_WEBHOOK_URL` or `DISCORD_WEBHOOK_URL`.
3. Optionally set `LANGUAGE` to `EN` or `FR` and `DESTINATION_CHANNEL` to the channel label you want displayed.
4. Confirm the `Weekly Friday 5pm` trigger is set to `0 17 * * 5`, then run `Run Now` once.
5. Activate the workflow after the summary posts to your webhook.

This workflow is a single-pass weekly reporter:

1. Trigger from either a manual run or the Friday 5pm schedule.
2. Build a config object from environment variables.
3. Fail fast if any required secret is missing.
4. Fetch the last 7 days of GitHub activity.
5. Generate a Markdown summary with Claude and send it to Slack or Discord.

## Node map

- `Run Now`
- `Weekly Friday 5pm`
- `Build Context`
- `Has Required Config`
- `Config Error`
- `Fetch GitHub Activity`
- `Build Claude Prompt`
- `Call Claude`
- `Build Webhook Payload`
- `Send Summary`

## Required variables

- `GITHUB_REPO`
- `GITHUB_TOKEN`
- `ANTHROPIC_API_KEY`
- `SLACK_WEBHOOK_URL` or `DISCORD_WEBHOOK_URL`

## Optional variables

- `LANGUAGE` - `EN` or `FR`
- `DELIVERY_PLATFORM` - `slack` or `discord`
- `ANTHROPIC_MODEL` - defaults to `claude-sonnet-4-20250514`
- `DESTINATION_CHANNEL` - used for the displayed label only

## Error handling

- Missing config throws from `Config Error`.
- GitHub 403 or 429 responses throw a rate-limit or permission message.
- Anthropic 401 responses throw a direct API-key message.
- Webhook delivery errors are surfaced with the upstream error text.

## Validation note

The exported JSON is designed to be importable into n8n as-is. This workspace does not ship a live n8n runtime, so the local validation here is limited to JSON structure and workflow shape.
