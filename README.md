# Weekly Dev Summary — n8n Workflow

Generates a weekly narrative summary of GitHub repo activity using Claude API.

## Setup

1. Import `weekly-dev-summary.json` into n8n
2. Add credentials:
   - **GitHub**: Personal access token with `repo` scope
   - **Anthropic**: Claude API key
   - **Slack**: Webhook URL or Slack app token
3. Configure variables in the workflow:
   - `repoUrl`: Your GitHub repo API URL
   - `channel`: Slack channel (default: `#dev-updates`)
4. Activate the workflow

## How It Works

| Step | Node | Description |
|------|------|-------------|
| 1 | Schedule Trigger | Runs every Friday at 5 PM |
| 2 | GitHub Commits | Fetches commits from the past 7 days |
| 3 | GitHub Issues & PRs | Fetches closed issues and merged PRs |
| 4 | Merge Activity | Combines data into a single payload |
| 5 | Claude Summary | Calls Claude API to generate narrative |
| 6 | Send to Slack | Posts summary to Slack channel |

## Output Example

> **Weekly Dev Summary**
> This week saw 23 commits across 5 contributors, with a focus on authentication refactoring and database optimization. 3 PRs were merged, including the long-awaited rate limiting middleware. 2 issues were closed related to session handling.
