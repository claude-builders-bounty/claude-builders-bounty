# Weekly GitHub Dev Summary — n8n Workflow

An n8n workflow that automatically generates a narrative development summary for any GitHub repository every Friday at 5 PM using Claude AI, and delivers it to a Discord channel via webhook.

## What it does

1. **Triggers** every Friday at 17:00 (cron: `0 17 * * 5`)
2. **Fetches from GitHub API** for the past 7 days:
   - Commits (`/repos/{owner}/{repo}/commits`)
   - Closed issues (`/repos/{owner}/{repo}/issues?state=closed`)
   - Merged pull requests (`/repos/{owner}/{repo}/pulls?state=closed`)
3. **Aggregates and formats** the data into a structured prompt
4. **Calls Claude API** (`claude-sonnet-4-20250514`) to generate a human-readable narrative summary
5. **Posts** the summary to a Discord channel as a rich embed via webhook

## Workflow Nodes

| Node | Type | Purpose |
|------|------|---------|
| Every Friday at 17:00 | Schedule Trigger | Cron trigger (`0 17 * * 5`) |
| Init Variables | Code | Computes date range, reads config vars |
| Fetch GitHub Commits | HTTP Request | `GET /repos/{owner}/{repo}/commits` |
| Fetch Closed Issues | HTTP Request | `GET /repos/{owner}/{repo}/issues?state=closed` |
| Fetch Merged PRs | HTTP Request | `GET /repos/{owner}/{repo}/pulls?state=closed` |
| Aggregate GitHub Data | Code | Merges and formats the three API responses |
| Build Claude Prompt | Code | Builds prompt with language setting |
| Call Claude API | HTTP Request | `POST https://api.anthropic.com/v1/messages` |
| Format Discord Message | Code | Formats Claude output as Discord embed |
| Send to Discord | HTTP Request | `POST {DISCORD_WEBHOOK_URL}` |

## Setup Instructions

### 1. Import the workflow

In n8n, go to **Workflows → Import from File** and select `workflow.json`.

### 2. Set n8n Variables

Go to **Settings → Variables** in n8n and create the following variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GITHUB_TOKEN` | Yes | GitHub Personal Access Token with `repo` scope | `ghp_xxxxxxxxxxxx` |
| `GITHUB_REPO` | Yes | Target repository in `owner/repo` format | `vercel/next.js` |
| `DISCORD_WEBHOOK_URL` | Yes | Full Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `CLAUDE_API_KEY` | Yes | Anthropic API key | `sk-ant-xxxxxxxxxxxx` |
| `SUMMARY_LANGUAGE` | No | Summary language: `EN` or `FR` (default: `EN`) | `EN` |

### 3. Create a GitHub Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Select the `repo` scope (or `public_repo` for public repos only)
4. Copy the token and set it as `GITHUB_TOKEN`

### 4. Create a Discord Webhook

1. In Discord, right-click your target channel → **Edit Channel**
2. Go to **Integrations → Webhooks → New Webhook**
3. Give it a name (e.g. "GitHub Dev Summary") and click **Copy Webhook URL**
4. Set the copied URL as `DISCORD_WEBHOOK_URL`

### 5. Get a Claude API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Navigate to **API Keys → Create Key**
3. Copy the key and set it as `CLAUDE_API_KEY`

### 6. Activate the workflow

Toggle the workflow to **Active** in n8n. It will run automatically every Friday at 17:00.

## Discord Output

The summary is delivered as a Discord embed containing:

- **Title**: `Weekly Dev Summary — owner/repo`
- **Description**: Narrative summary in Markdown (up to 4000 characters)
- **Fields**: Period, commit count, closed issues, merged PRs, language
- **Footer**: `Powered by Claude (claude-sonnet-4-20250514) via n8n`
- **Timestamp**: When the summary was generated

Example embed appearance:

```
Weekly Dev Summary — vercel/next.js
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This week saw significant activity in the repository, with 12 commits...

[narrative continues]

Period: 2025-05-09 → 2025-05-16  |  Commits: 12  |  Closed Issues: 4
Merged PRs: 3  |  Language: EN

Powered by Claude (claude-sonnet-4-20250514) via n8n
```

## Configuration Options

### Change schedule

Edit the **Every Friday at 17:00** node and update the cron expression:
- `0 17 * * 5` — Friday 5 PM UTC (default)
- `0 9 * * 1` — Monday 9 AM UTC
- `0 8 * * 1,5` — Monday and Friday 8 AM UTC

### Change language

Set `SUMMARY_LANGUAGE` to:
- `EN` — English summary (default)
- `FR` — French summary

### Change target repository

Update `GITHUB_REPO` to any `owner/repo` value. The workflow works with both public and private repositories (private requires appropriate token scopes).

### Change target Discord channel

Create a new webhook in a different channel and update `DISCORD_WEBHOOK_URL`.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| GitHub API returns 401 | Check `GITHUB_TOKEN` is valid and has `repo` scope |
| GitHub API returns 404 | Check `GITHUB_REPO` format is exactly `owner/repo` |
| Claude returns error | Verify `CLAUDE_API_KEY` is valid and has sufficient credits |
| Discord returns 404 | Verify `DISCORD_WEBHOOK_URL` — webhook may have been deleted |
| No commits/issues/PRs found | Normal if the repo had no activity; summary will still be generated |

## Requirements

- n8n v1.0+ (uses `scheduleTrigger` typeVersion 1.2 and `httpRequest` typeVersion 4.2)
- GitHub Personal Access Token (repo scope)
- Anthropic API key with access to `claude-sonnet-4-20250514`
- Discord webhook URL
