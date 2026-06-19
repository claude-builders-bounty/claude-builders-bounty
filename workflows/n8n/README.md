# Weekly GitHub Dev Summary – n8n + Claude Workflow

Automatically generates a weekly narrative summary of a GitHub repo's activity using Claude API.

## Features
- ✅ Weekly cron trigger (Friday 5pm)
- ✅ Fetches commits, closed issues, merged PRs from GitHub API
- ✅ Generates narrative summary via Claude API
- ✅ Sends summary to Discord/Slack webhook
- ✅ Configurable: repo, language (EN/FR), webhook URL

## Setup (5 steps)
1. **Import** `weekly-dev-summary.json` into n8n
2. **Configure credentials**: GitHub token, Anthropic API key
3. **Set variables**: `repo`, `language`, `webhook_url`
4. **Test** with manual execution
5. **Activate** the workflow

## Requirements
- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token
- Anthropic API key
- Discord/Slack webhook URL

## Configuration Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `repo` | GitHub repo (owner/name) | `Spectral-Finance/lux` |
| `language` | Summary language (EN/FR) | `EN` |
| `webhook_url` | Discord/Slack webhook | `https://discord.com/api/webhooks/...` |
| `github_token` | GitHub PAT | `ghp_xxxxxxxxxxxx` |
| `anthropic_api_key` | Anthropic API key | `sk-ant-xxxxxxxxxxxx` |
