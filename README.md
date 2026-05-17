# Weekly GitHub Dev Summary — n8n + Claude AI

Automated workflow that generates a narrative weekly summary of GitHub repository activity using Claude AI.

## Setup (5 steps)

1. **Import workflow** — Open n8n, click "Import from File", select `weekly-dev-summary.json`
2. **Configure variables** — Set `repo_url`, `github_token`, `anthropic_api_key`, `webhook_url`, `language` (EN/FR)
3. **Activate workflow** — Click "Active" toggle
4. **Test manually** — Click "Execute Workflow" to verify
5. **That's it** — Runs every Friday at 5pm automatically

## What it does

1. **Triggers** every Friday at 5pm (configurable cron)
2. **Fetches** from GitHub API: commits, closed issues, merged PRs (past week)
3. **Aggregates** data into a summary object
4. **Generates** narrative summary via Claude API (`claude-sonnet-4-20250514`)
5. **Sends** to Slack/Discord webhook (also supports email)

## Configurable variables

| Variable | Description |
|----------|-------------|
| `repo_url` | GitHub API repo URL (e.g. `https://api.github.com/repos/owner/repo`) |
| `github_token` | GitHub Personal Access Token |
| `anthropic_api_key` | Anthropic Claude API key |
| `webhook_url` | Discord or Slack webhook URL |
| `language` | `EN` for English, `FR` for French |

## Requirements

- [n8n](https://n8n.io) instance (self-hosted or cloud)
- GitHub Personal Access Token
- Anthropic API key
