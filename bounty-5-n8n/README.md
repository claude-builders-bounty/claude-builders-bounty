# Weekly GitHub Dev Summary — n8n + Claude API

Automated weekly narrative summary of a GitHub repo's activity, powered by Claude claude-sonnet-4-20250514 and delivered to Discord.

## What it does

Every Friday at 5pm the workflow:
1. Fetches the last 7 days of commits, closed issues, and merged PRs from GitHub
2. Aggregates the data into a structured prompt
3. Calls Claude claude-sonnet-4-20250514 to write a 200-300 word narrative summary
4. Posts the summary as a Discord embed

## Setup (5 steps)

**1. Import the workflow**
In n8n: *Workflows → Import from file* → select `weekly_dev_summary.json`

**2. Create credentials**

| Name | Type | Value |
|---|---|---|
| `GitHub Token` | HTTP Header Auth | Header: `Authorization`, Value: `Bearer ghp_...` |
| `Anthropic API Key` | HTTP Header Auth | Header: `x-api-key`, Value: your Anthropic key |

**3. Set workflow variables** (n8n Settings → Variables)

| Variable | Example | Description |
|---|---|---|
| `GITHUB_REPO` | `tari-project/universe` | Target repo (`owner/repo`) |
| `LANGUAGE` | `EN` or `FR` | Summary language |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Destination webhook |

**4. Activate the workflow**

Toggle the workflow to *Active* — it will run every Friday at 17:00 (cron: `0 17 * * 5`).

**5. Test manually**

Click *Test Workflow* to run immediately and confirm the Discord message arrives.

## Configurable variables

All three variables (`GITHUB_REPO`, `LANGUAGE`, `DISCORD_WEBHOOK_URL`) are read from n8n workflow variables — change them without touching the workflow JSON.

## Example output

> **Weekly Dev Summary — tari-project/universe**
>
> This week the team merged 12 PRs and closed 8 issues. The highlight was the landing of the auto-start Windows fix (#1588) by @possum, which resolves a bug that had persisted across 100+ versions. The mining dashboard received a hashrate unit correction for macOS users, and three documentation improvements were merged to clarify the Linux build path...

## Requirements

- n8n 1.x (tested on 1.91)
- GitHub Personal Access Token (read:repo scope)
- Anthropic API key
- Discord webhook URL
