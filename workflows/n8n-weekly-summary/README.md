# n8n + Claude — Automated Weekly Dev Summary

A complete n8n workflow that generates a narrative weekly summary of your GitHub repo's activity using Claude AI.

## What It Does

Every Friday at 5pm, the workflow:
1. Fetches commits, closed issues, and merged PRs from the past 7 days
2. Sends the data to Claude for narrative summarization
3. Delivers the summary to Discord or Slack via webhook

## Setup (5 steps)

### 1. Import the workflow
- Open n8n → Workflows → Import from File
- Select `workflow.json`

### 2. Configure credentials

**GitHub Token:**
- Settings → Credentials → Add → Header Auth
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer ghp_your_token_here`

**Anthropic API Key:**
- Settings → Credentials → Add → Header Auth
- Name: `Anthropic API Key`
- Header Name: `x-api-key`
- Header Value: `sk-ant-your_key_here`

### 3. Set environment variables
In n8n Settings → Environment Variables:

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `GITHUB_REPO` | Yes | `octocat/hello-world` | Repository to summarize |
| `WEBHOOK_URL` | Yes | `https://discord.com/api/webhooks/...` | Discord/Slack webhook URL |
| `SUMMARY_LANGUAGE` | No | `EN` or `FR` | Summary language (default: EN) |

### 4. Activate the workflow
Toggle the workflow to "Active" in n8n.

### 5. Test it
Click "Execute Workflow" to run immediately and verify the output.

## Configurable Variables

| Variable | Default | Options |
|----------|---------|---------|
| `GITHUB_REPO` | `octocat/hello-world` | Any `owner/repo` |
| `SUMMARY_LANGUAGE` | `EN` | `EN`, `FR` |
| `WEBHOOK_URL` | — | Discord or Slack webhook URL |
| Cron schedule | Friday 5pm | Edit the Schedule Trigger node |
| Claude model | `claude-sonnet-4-20250514` | Any Anthropic model |

## Delivery Options

### Discord
Use a Discord webhook URL:
```
https://discord.com/api/webhooks/1234567890/abcdef...
```
The payload format `{ "content": "..." }` works natively with Discord.

### Slack
Use a Slack Incoming Webhook:
```
https://hooks.slack.com/services/T00/B00/xxx
```
Change the webhook body in the "Send to Discord/Slack" node to:
```json
{ "text": "{{ $json.summary }}" }
```

## Workflow Architecture

```
┌─────────────┐     ┌───────────────┐     ┌──────────────┐
│ Cron Trigger│────▶│ Set Config    │────▶│ Fetch Commits│
│ (Fri 5pm)  │     │ (repo, lang)  │  │  │ Fetch Issues │
└─────────────┘     └───────────────┘  │  │ Fetch PRs    │
                                        │  └──────┬───────┘
                                        │         │
                                        │  ┌──────▼───────┐
                                        │  │ Merge Data   │
                                        │  └──────┬───────┘
                                        │         │
                                        │  ┌──────▼───────┐
                                        └──│ Build Prompt │
                                           └──────┬───────┘
                                                  │
                                           ┌──────▼───────┐
                                           │ Call Claude  │
                                           └──────┬───────┘
                                                  │
                                           ┌──────▼───────┐
                                           │ Send Webhook │
                                           └──────────────┘
```

## Sample Output

See `sample-output.md` for an example of what the weekly summary looks like.

## Requirements

- n8n v1.0+ (self-hosted or cloud)
- GitHub Personal Access Token (read access to repos)
- Anthropic API key
- Discord or Slack webhook URL
