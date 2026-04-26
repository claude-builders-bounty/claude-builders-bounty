# WORKFLOW: n8n + Claude Code — Automated Weekly Dev Summary

> Bounty #5 — $200 | [Issue Link](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

## Setup (5 steps)

### 1. Import the workflow
- Open n8n dashboard
- Click **"Add workflow"** > **"Import from file"**
- Select `workflow.json`

### 2. Set up GitHub credentials
- In n8n: **Settings > Credentials > Add > Header Auth**
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer ghp_your_github_token`

### 3. Set up Anthropic credentials
- In n8n: **Settings > Credentials > Add > Header Auth**
- Name: `Anthropic API Key`
- Header Name: `x-api-key`
- Header Value: `sk-ant-your-key`

### 4. Set environment variables
In n8n: **Settings > Variables**, add:

| Variable | Value | Example |
|----------|-------|---------|
| `GITHUB_REPO` | `owner/repo` | `xamdkx/quantlab` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `SLACK_WEBHOOK_URL` | Slack webhook URL (optional) | `https://hooks.slack.com/...` |
| `SUMMARY_LANGUAGE` | `EN` or `FR` | `EN` |

### 5. Activate the workflow
Toggle the workflow **Active**. It runs every Friday at 5pm.

To test immediately: click **"Execute Workflow"** in n8n.

## What it does

```
Every Friday at 5pm
    ↓
Fetch from GitHub API (parallel):
    ├── Commits (last 7 days)
    ├── Closed issues (last 7 days)
    └── Merged PRs (last 7 days)
    ↓
Combine & build Claude prompt
    ↓
Call Claude Sonnet → generate narrative summary
    ↓
Deliver via:
    ├── Discord webhook
    └── Slack webhook (optional)
```

## Requirements (all met)

- [x] Exportable n8n workflow (importable .json file)
- [x] Trigger: weekly cron (Friday at 5pm)
- [x] Fetches from GitHub API: commits, closed issues, merged PRs
- [x] Calls Claude API (`claude-sonnet-4-20250514`) for narrative summary
- [x] Delivers via Discord webhook (+ Slack as bonus)
- [x] Configurable variables: GitHub repo, destination channel, language (EN/FR)
- [x] README with 5-step setup

## Output format

The summary includes:

1. **Highlights** — Top 3 most impactful changes
2. **What shipped** — Features and fixes that went out
3. **What's in progress** — Based on open issues context
4. **Stats** — Commits, PRs merged, issues closed
5. **Contributors** — Who contributed this week

## Bonus features

- **Dual delivery** — Discord AND Slack simultaneously
- **Bilingual** — English and French support via `SUMMARY_LANGUAGE` variable
- **Parallel fetching** — commits, issues, and PRs fetched simultaneously (faster)
- **Smart truncation** — handles Discord's 2000-char limit and Slack's 3000-char limit
- **Merged PR filtering** — only includes actually merged PRs, not just closed ones
- **Claude model configurable** — easy to swap to Opus or Haiku in the HTTP node
- **Bot avatar** — Discord messages show Claude's icon

## Workflow nodes

| Node | Type | Purpose |
|------|------|---------|
| Weekly Trigger | Schedule | Fires every Friday 5pm |
| Fetch Commits | HTTP Request | GitHub API — commits last 7 days |
| Fetch Closed Issues | HTTP Request | GitHub API — closed issues last 7 days |
| Fetch Merged PRs | HTTP Request | GitHub API — merged PRs last 7 days |
| Merge All Data | Merge | Combines the 3 data streams |
| Prepare Claude Prompt | Code | Builds structured prompt with EN/FR support |
| Call Claude API | HTTP Request | Anthropic messages API |
| Format Summary | Code | Adds header, footer, date |
| Send to Discord | HTTP Request | Discord webhook delivery |
| Send to Slack | HTTP Request | Slack webhook delivery |

## Files

| File | Purpose |
|------|---------|
| `workflow.json` | n8n workflow (import this) |
| `README.md` | This file |
| `HOW-TO.md` | Detailed customization guide |
