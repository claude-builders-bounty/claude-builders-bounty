# n8n Weekly Dev Summary Workflow

Automated weekly narrative summary of GitHub repository activity via Claude API.

## Install

1. Import `weekly-dev-summary.json` into n8n
2. Set env variables: `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `SMTP_FROM`, `NOTIFY_EMAIL`
3. Activate workflow

## How It Works

- **Trigger:** Weekly cron (Friday 5pm)
- **Fetch:** Commits, closed issues, merged PRs from GitHub API
- **Summarize:** Claude API generates narrative summary
- **Deliver:** Email with formatted summary
