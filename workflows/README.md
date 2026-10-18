# n8n Weekly Dev Summary Workflow

Generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

## Setup (5 steps)

1. Import `n8n-weekly-dev-summary.json` into your n8n instance.
2. Set environment variables / n8n variables:
   - `GITHUB_REPO` (e.g. `owner/repo`)
   - `ANTHROPIC_API_KEY`
   - `DELIVERY_WEBHOOK` (Slack/Discord/email webhook URL)
   - `LANGUAGE` (`EN` or `FR`)
   - `WEEK_START` (ISO date, updated weekly by cron or manually)
3. Configure GitHub credentials in n8n (for the HTTP Request nodes).
4. Activate the workflow.
5. Wait for the Friday 5pm cron (or trigger manually) and check your delivery channel.

## Configurable variables

| Variable | Description |
|---|---|
| `GITHUB_REPO` | Target repository (`owner/repo`) |
| `DELIVERY_WEBHOOK` | Destination channel webhook |
| `LANGUAGE` | Summary language (`EN` or `FR`) |

## Delivery

Summary is delivered via the configured webhook (Slack/Discord/email gateway). Claude model used: `claude-sonnet-4-20250514`.

## Sample

See the workflow JSON for the full node graph. Execution screenshot to be added after first successful run.