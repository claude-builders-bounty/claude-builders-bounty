# n8n Weekly Dev Summary Workflow

Automated weekly narrative summary of GitHub repo activity using n8n + Claude API.

## Setup (5 steps)

1. **Import workflow**: In n8n, go to *Workflows* → *Import from File* → select `workflow.json`
2. **Set credentials**: Add your GitHub Personal Access Token and Anthropic API key in *Settings* → *Credentials*
3. **Configure variables**: Open the *Set Variables* node and set `repo`, `owner`, `webhookUrl`, and `language` (EN/FR)
4. **Activate**: Toggle the workflow to *Active* in the top-right corner
5. **Test**: Click *Execute Workflow* or wait for the weekly cron trigger (Fridays at 5 PM)

## Delivery

The summary is sent via Discord webhook (configurable to Slack by changing the HTTP Request node URL).

## Required Credentials

- `githubApi` — GitHub Personal Access Token with `repo` scope
- `anthropicApi` — Anthropic API key

## Workflow Overview

1. **Cron Trigger** — Every Friday at 17:00
2. **Set Variables** — Configurable repo, language, webhook
3. **GitHub Commits** — Fetch commits from the past 7 days
4. **GitHub Issues** — Fetch closed issues from the past 7 days
5. **GitHub PRs** — Fetch merged PRs from the past 7 days
6. **Format Data** — Combine and format data for Claude
7. **Claude API** — Generate narrative summary
8. **Discord Webhook** — Deliver the summary

## Customization

| Variable | Description | Example |
|----------|-------------|---------|
| `owner` | GitHub organization or user | `claude-builders-bounty` |
| `repo` | Repository name | `claude-builders-bounty` |
| `language` | Summary language | `EN` or `FR` |
| `webhookUrl` | Discord/Slack webhook URL | `https://discord.com/api/webhooks/...` |