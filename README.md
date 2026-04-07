# n8n + Claude: Automated Weekly Dev Summary

Generates narrative weekly dev summaries from GitHub activity using Claude AI.

## Setup (5 steps)

### 1. Import
n8n > Workflows > Import > select `weekly-dev-summary.json`

### 2. GitHub credentials
Credentials > New > Header Auth: `Authorization` = `Bearer YOUR_GITHUB_PAT`

### 3. Set variables
| Variable | Example |
|---|---|
| `GITHUB_REPO` | `facebook/react` |
| `CLAUDE_API_KEY` | `sk-ant-...` |
| `WEBHOOK_URL` | Discord/Slack webhook |
| `LANGUAGE` | `EN` or `FR` |

### 4. Test
Execute Workflow manually.

### 5. Activate
Toggle Active. Default: Friday 5pm.

## Features
- Weekly cron trigger
- GitHub commits, issues, PRs (7 days)
- Claude claude-sonnet-4-20250514 narrative summary
- EN/FR support
- Discord/Slack delivery
- Configurable via variables

Closes #5
