# n8n Weekly Dev Summary Workflow

Automatically generates a weekly narrative summary of GitHub repo activity using Claude API.

## Features
- Weekly cron trigger (Friday 5pm)
- Fetches commits, closed issues, merged PRs from GitHub API
- Calls Claude API to generate narrative summary
- Delivers via Discord webhook (or email)
- Configurable: repo, channel, language (EN/FR)

## Setup (5 steps)
1. Import `weekly-dev-summary.json` into n8n
2. Set GitHub token in credentials
3. Set Claude API key in credentials
4. Configure `REPO_OWNER` and `REPO_NAME` variables
5. Set your Discord webhook URL or email

## Configuration
Edit the workflow variables node to customize:
- `repo_owner`: GitHub username/org
- `repo_name`: Repository name
- `discord_webhook`: Discord webhook URL
- `language`: "en" or "fr"
