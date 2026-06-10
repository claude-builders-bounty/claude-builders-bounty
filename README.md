# n8n Weekly Dev Summary Workflow

Automated weekly narrative summary of GitHub repo activity using Claude API.

## Setup
1. Import `n8n-weekly-dev-summary.json` into n8n
2. Set env vars: `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`
3. Configure `repo` and `notifyUrl` in the Cron node
4. Activate workflow

## Schedule
Runs every Friday at 5pm UTC via cron trigger.

## Output
- Fetches commits, closed issues, merged PRs from GitHub API
- Aggregates into a structured prompt
- Calls Claude Sonnet 4 to generate narrative summary
- Posts to Slack/Discord webhook
