# GitHub Weekly Summary — n8n + Claude API Workflow

Automatically generates a narrative weekly summary of your GitHub repository's activity using Claude, delivered to Discord or Slack.

## Features

- 🕐 **Weekly cron trigger** (Fridays at 5pm UTC)
- 📊 **Fetches:** commits, closed issues, merged PRs
- 🤖 **Claude API** generates engaging narrative summaries
- 📨 **Delivers** to Discord webhook or Slack
- 🌍 **Configurable** repo, channel, and language (EN/FR)
- 🔧 **5-step setup**

## Setup (5 steps)

### 1. Prerequisites
- n8n instance (cloud or self-hosted)
- GitHub personal access token (repo scope)
- Anthropic API key
- Discord webhook URL (or Slack incoming webhook)

### 2. Import the workflow
```bash
# In n8n UI: Settings → Import from file → select github-weekly-summary.json
```

### 3. Configure credentials
In n8n, create these credentials:
- **GitHub Auth:** HTTP Header Auth → `Authorization: token YOUR_GITHUB_TOKEN`
- **Claude Auth:** HTTP Header Auth → `x-api-key: YOUR_ANTHROPIC_KEY`

### 4. Set environment variables
```bash
GITHUB_REPO=owner/repo-name
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
SUMMARY_LANG=EN  # or FR
```

### 5. Activate
Toggle the workflow to active. It will run every Friday at 5pm UTC.

## Workflow Structure

```
Weekly Trigger → Set Variables → [Fetch Commits / Issues / PRs] → Summarize Data → Call Claude API → Send to Discord/Slack
```

## Sample Output

> ## 📊 Weekly Dev Summary — week of March 24, 2026
> 
> 🎉 **23 commits** pushed by 4 contributors!
> 
> ### Highlights
> - ✅ **5 issues closed** including the long-awaited dark mode (#42)
> - 🔀 **3 PRs merged** — new auth flow, performance fixes, docs update
> - 🚀 Major milestone: v2.0 release prep is underway
> 
> Big thanks to @alice for crushing 12 commits this week! 💪

## Customization

- Change cron schedule in the Weekly Trigger node
- Modify the Claude prompt to match your team's voice
- Add email delivery by replacing Discord node with Send Email node
