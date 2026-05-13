# Weekly GitHub Summary via Claude API — n8n Workflow

An n8n workflow that automatically generates a narrative weekly summary of your GitHub repo's activity using the Claude API, delivered to Discord.

## What It Does

Every Friday at 5pm, this workflow:

1. Fetches the past 7 days of **commits**, **closed issues**, and **merged PRs** from the GitHub API
2. Sends the raw data to **Claude** (`claude-sonnet-4-20250514`) with a prompt to write a narrative summary
3. Posts the summary to a **Discord channel** via webhook

## Setup (5 steps)

### 1. Import the workflow

Open your n8n instance → **Workflows** → **Import from File** → select `workflow.json`.

### 2. Configure GitHub token

Go to **Credentials** → **Create New** → **Header Auth**:
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer ghp_YOUR_GITHUB_TOKEN`

Create a token at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope.

### 3. Configure Claude API key

Set the environment variable `ANTHROPIC_API_KEY` in your n8n instance:

```bash
# docker-compose.yml
environment:
  - ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Or set it in **Settings** → **Environment Variables** if using n8n Cloud.

Get your key at [console.anthropic.com](https://console.anthropic.com/).

### 4. Set your repo and Discord webhook

Set these environment variables in n8n:

| Variable | Example | Description |
|----------|---------|-------------|
| `GITHUB_OWNER` | `vercel` | GitHub org or username |
| `GITHUB_REPO` | `next.js` | Repository name |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Discord channel webhook URL |
| `SUMMARY_LANGUAGE` | `EN` or `FR` | Summary language |

To create a Discord webhook: Server Settings → Integrations → Webhooks → New Webhook.

### 5. Activate the workflow

Toggle the workflow to **Active**. It will run every Friday at 5pm.

To test immediately: click **Execute Workflow** manually.

## Workflow Architecture

```
┌──────────────┐    ┌────────────┐    ┌──────────────────┐
│ Cron Trigger │───▶│   Config   │───▶│  GitHub API x3   │
│ Fri 5pm      │    │ Variables  │    │ commits/issues/  │
└──────────────┘    └────────────┘    │ merged PRs       │
                                      └────────┬─────────┘
                                               │
                                      ┌────────▼─────────┐
                                      │   Merge Data     │
                                      └────────┬─────────┘
                                               │
                                      ┌────────▼─────────┐
                                      │  Claude API      │
                                      │  Generate Summary│
                                      └────────┬─────────┘
                                               │
                                      ┌────────▼─────────┐
                                      │ Discord Webhook  │
                                      │ Post Summary     │
                                      └──────────────────┘
```

## Configurable Variables

| Variable | Default | Options |
|----------|---------|---------|
| `GITHUB_OWNER` | `your-org` | Any GitHub user/org |
| `GITHUB_REPO` | `your-repo` | Any public/private repo |
| `SUMMARY_LANGUAGE` | `EN` | `EN` (English), `FR` (French) |
| `DISCORD_WEBHOOK_URL` | — | Discord webhook URL |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |

## Switching to Slack

Replace the Discord webhook node with a Slack webhook:
- Change the `Send to Discord` node's URL to your Slack webhook URL
- The payload format is compatible — Slack accepts `content` as `text`:

```json
{ "text": "{{ $json.summary }}" }
```

## Sample Output

> ## Weekly Dev Summary — vercel/next.js
>
> **Highlights**: This week saw significant performance improvements to the App Router and a critical fix for middleware...
>
> **What shipped**: 12 PRs merged including improved ISR cache invalidation (#58432) and...
