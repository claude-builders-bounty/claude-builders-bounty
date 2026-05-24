# Weekly Dev Summary — n8n + Claude

Automated weekly narrative summary of GitHub repo activity, delivered via Discord/Slack webhook.

## Setup (5 steps)

1. **Import workflow** — In n8n: *Workflows → Import from File* → select `weekly-dev-summary.json`.

2. **Add credentials**
   - **GitHub API** — personal access token with `repo` read scope (attach to the three GitHub HTTP nodes).
   - **HTTP Header Auth** for Claude — header name `x-api-key`, value = your Anthropic API key.

3. **Set environment variables** in n8n (*Settings → Variables* or `.env`):

   | Variable | Example | Description |
   |----------|---------|-------------|
   | `GITHUB_OWNER` | `claude-builders-bounty` | Repo owner |
   | `GITHUB_REPO` | `claude-builders-bounty` | Repo name |
   | `SUMMARY_LANGUAGE` | `EN` or `FR` | Summary language |
   | `DELIVERY_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Discord or Slack incoming webhook |

4. **Activate** the workflow (cron: **Friday 5:00 PM** server time).

5. **Test** — Click *Execute Workflow* manually and confirm the webhook receives the summary.

## What it does

- **Trigger:** Weekly cron (`0 17 * * 5`)
- **Fetches:** commits, closed issues, merged PRs for the last 7 days
- **Calls:** Claude API (`claude-sonnet-4-20250514`) for a narrative summary
- **Delivers:** Markdown payload to your configured webhook

## Sample test run

See [`sample-output/test-execution-log.json`](sample-output/test-execution-log.json) for a dry-run against `claude-builders-bounty/claude-builders-bounty` (stats + Claude prompt payload).

## Delivery format

The webhook receives JSON:

```json
{
  "content": "## Weekly Dev Summary — owner/repo\n\n**TL;DR stats:** ...\n\n<narrative>"
}
```

Works with Discord webhooks out of the box. For Slack, add a small Format node or use Slack's `{ "text": "..." }` wrapper.

## Bounty

Submitted for [issue #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5).
