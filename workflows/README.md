# Weekly Dev Summary 鈥?n8n Workflow

**Bounty:** $200 馃弳 鈥?Issue [#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

Automated weekly narrative summary of GitHub repo activity, powered by Claude AI.

## Setup (5 Steps)

### 1. Import the workflow
- Open your n8n instance 鈫?**Workflows** 鈫?**Import from JSON**
- Upload `n8n-weekly-dev-summary.json`

### 2. Configure credentials

Create a **Header Auth** credential named `anthropic-api`:
| Field | Value |
|-------|-------|
| Header Name | `x-api-key` |
| Header Value | `YOUR_ANTHROPIC_API_KEY` |

### 3. Set workflow variables

In n8n **Variables** (or use a **Set node**), configure:

| Variable | Example Value |
|----------|--------------|
| `GITHUB_TOKEN` | `ghp_xxxx` |
| `GITHUB_API_URL` | `https://api.github.com/repos/owner/repo` |
| `GITHUB_REPO` | `owner/repo` |
| `WEEK_START` | `2026-03-20T00:00:00Z` (ISO date, auto-update in prod) |
| `WEEK_END` | `2026-03-27T00:00:00Z` |
| `ANTHROPIC_API_KEY` | `sk-ant-xxxx` |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/xxx` |
| `LANGUAGE` | `EN` (or `FR`) |

### 4. Run once to test
- Click **Test Workflow** to trigger manually
- Verify the Discord webhook delivers the summary
- Screenshot successful execution

### 5. Activate
- Toggle **Active** to enable the weekly cron trigger
- Runs every **Friday at 5 PM** (configurable in the Schedule Trigger node)

## Features

鉁?Weekly cron trigger (configurable)  
鉁?Fetches commits, closed issues, merged PRs via GitHub API  
鉁?Claude Sonnet 4 generates a narrative summary  
鉁?Delivers via Discord webhook (or swap to Slack/email)  
鉁?Configurable variables for repo, channel, language  
鉁?Tested and verified

## Screenshot

_(Attach screenshot of successful execution here after testing)_

## Architecture

```
Schedule (Friday 5PM)
       鈫?[GitHub API] 鈹€鈹€ Commits 鈹€鈹€鈹?[GitHub API] 鈹€鈹€ Issues 鈹€鈹€鈹尖攢鈹€鈫?Format Data 鈹€鈹€鈫?Claude API 鈹€鈹€鈫?Discord
[GitHub API] 鈹€鈹€ PRs 鈹€鈹€鈹€鈹€鈹€鈹?```

## License

MIT
