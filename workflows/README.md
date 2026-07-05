# Weekly GitHub Dev Summary — n8n Workflow

An n8n workflow that automatically generates a weekly development summary using the Claude API.

## Features

- Scheduled every Friday at 5pm
- Fetches commits, closed issues, and merged PRs from GitHub
- Generates a narrative summary via Claude API
- Delivers via email

## Installation (5 steps)

1. Install n8n: `npx n8n start`
2. Open http://localhost:5678 and create an account
3. Import the workflow: Settings > Import > `n8n-weekly-summary.json`
4. Configure credentials: GitHub (token), Anthropic (API key), Email (SMTP)
5. Set your repo in the "Set Repo Config" node: `bambooshadow-studio/mcp-power-pack`

## Configurable Variables

| Variable | Where to set | Default |
|---|---|---|
| GitHub repo | Set Repo Config node | `owner/repo` |
| Destination email | Send Email node | Your email |
| Language | Set workflow variables | EN |

## Requirements

- n8n >= 2.0
- GitHub token (public repo access)
- Anthropic API key
- SMTP credentials (for email delivery)

## Workflow Structure

```
Weekly Cron (Fri 5pm)
    ↓
GitHub API: Commits (last 7 days)
    ↓
GitHub API: Closed Issues (last 7 days)
    ↓
GitHub API: Merged PRs (last 7 days)
    ↓
Merge & Format
    ↓
Claude API: Generate Summary
    ↓
Format Output
    ↓
Send Email
```
