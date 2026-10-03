# Automated Weekly GitHub Dev Summary via Claude API (n8n Workflow)

An automated n8n workflow that triggers weekly to fetch commits and closed PRs from GitHub API, generates an executive narrative summary using Claude API (`claude-sonnet-4-20250514`), and delivers the report to Discord / Slack webhooks.

## Setup in 4 Steps
1. Import `workflows/n8n/github_weekly_summary.json` into your n8n instance.
2. Set workflow variable `GITHUB_REPO` (e.g. `owner/repo`).
3. Configure `ANTHROPIC_API_KEY` credential in the Claude API node.
4. Set `WEBHOOK_URL` to your Discord or Slack channel webhook.
