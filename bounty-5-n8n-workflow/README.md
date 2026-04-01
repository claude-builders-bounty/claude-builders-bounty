# Bounty 5 — n8n + Claude API Weekly Dev Summary

An exportable n8n workflow that generates a narrative weekly development summary using GitHub data and the Claude API, delivered via Discord webhook.

## Setup (4 steps)

1. **Import the workflow** — In n8n, go to Workflows > Import from File > select `weekly-summary.json`

2. **Set environment variables** in n8n Settings > Variables:

   | Variable | Description | Example |
   |----------|-------------|---------|
   | `GITHUB_REPO` | Repository in `owner/repo` format | `acme/webapp` |
   | `GITHUB_TOKEN` | GitHub personal access token (read-only) | `ghp_xxxx` |
   | `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-xxxx` |
   | `DISCORD_WEBHOOK_URL` | Discord channel webhook URL | `https://discord.com/api/webhooks/...` |
   | `SUMMARY_LANGUAGE` | Output language: `EN` or `NL` | `EN` |

3. **Activate the workflow** — toggle the Active switch in n8n

4. **Test** — click "Execute Workflow" to run it immediately

## What it does

| Step | Node | Description |
|------|------|-------------|
| 1 | **Weekly Trigger** | Fires every Friday at 5:00 PM (cron: `0 17 * * 5`) |
| 2 | **Load Configuration** | Reads repo, token, and language from environment variables |
| 3 | **Fetch GitHub Data** | Three parallel API calls: commits, closed issues, merged PRs (last 7 days) |
| 4 | **Merge Data** | Combines all GitHub data into a single structured payload |
| 5 | **Claude API** | Sends the data to `claude-sonnet-4-20250514` with a prompt to generate a narrative summary |
| 6 | **Extract Summary** | Pulls the text from Claude's response |
| 7 | **Discord Webhook** | Posts the summary to a Discord channel |

## How it works

### GitHub data collection

The workflow fetches three types of data from the GitHub API in parallel:

- **Commits** — all commits from the last 7 days, extracted to short SHA, message, author, and date
- **Closed issues** — filtered to exclude pull requests (GitHub API returns PRs mixed with issues)
- **Merged PRs** — closed PRs filtered to only those with a `merged_at` timestamp

### Claude API summarization

The prompt instructs Claude to write a team-friendly narrative summary in Markdown with these sections:

- **Highlights** — 2-3 key achievements
- **Commits** — grouped by theme (not listed individually)
- **Issues Resolved** — with numbers and brief descriptions
- **PRs Merged** — with numbers, titles, and authors
- **Looking Ahead** — forward-looking note based on open work

The language parameter (`EN` or `NL`) controls whether the summary is in English or Dutch.

### Discord delivery

The summary is posted via webhook. Long summaries are split between the message `content` field (first 1900 chars) and an embed (remaining text) to stay within Discord's character limits.

## Configuration

### Change the schedule

Edit the cron expression in the "Weekly Trigger" node. Examples:

| Schedule | Cron expression |
|----------|----------------|
| Friday 5pm (default) | `0 17 * * 5` |
| Monday 9am | `0 9 * * 1` |
| Daily 6pm | `0 18 * * *` |

### Change the destination

Replace the "Send to Discord" node with any n8n node:

- **Slack** — use the Slack node with a webhook URL
- **Email** — use the Send Email node
- **Microsoft Teams** — use the Teams webhook node
- **Custom webhook** — use the HTTP Request node

### Change the AI model

Edit the `model` field in the "Claude API" node's JSON body. Compatible models:

- `claude-sonnet-4-20250514` (default — good balance of quality and speed)
- `claude-opus-4-20250514` (higher quality, slower)
- `claude-haiku-4-20250514` (faster, cheaper)

## Sample output

See [samples/sample-summary.md](samples/sample-summary.md) for an example of the generated summary.

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub personal access token with `repo` scope (or fine-grained with read access to commits, issues, PRs)
- Anthropic API key
- Discord webhook URL (or alternative destination)
