# Weekly Dev Summary — n8n + Claude Workflow

Automated weekly GitHub activity digest powered by Claude API.

## Setup (5 Steps)

1. **Import workflow** into n8n: drag-and-drop `weekly-dev-summary.json` or use Import from File
2. **Configure credentials**:
   - `github_token`: GitHub personal access token with `repo` scope
   - `anthropic_api_key`: Anthropic API key from console.anthropic.com
3. **Set repo URL**: edit the Cron node's parameters or use n8n's workflow variables
4. **Set webhook URL**: point to your Discord/Slack incoming webhook
5. **Activate** the workflow — it runs every Friday at 5pm

## Configurable Variables

| Variable | Default | Description |
|---|---|---|
| `repo_url` | (required) | GitHub API repo URL (e.g., `https://api.github.com/repos/owner/repo`) |
| `github_token` | (required) | GitHub PAT with repo access |
| `anthropic_api_key` | (required) | Anthropic API key |
| `webhook_url` | (required) | Discord/Slack webhook URL |
| `language` | EN | Summary language (EN / FR) |
| `since` | auto (7 days ago) | Start of reporting period |
| `until` | auto (now) | End of reporting period |

## What It Does

- Runs every Friday at 5pm (configurable cron)
- Fetches commits, closed issues, and merged PRs from GitHub API
- Structures the data and sends it to Claude Sonnet 4
- Claude generates a narrative weekly summary in Markdown
- Posts the summary to your Discord/Slack channel
