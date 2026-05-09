# n8n Weekly Dev Summary Bot

Automatically generate a narrative weekly development summary for any GitHub repository using Claude API, delivered to Discord or Slack.

## What It Does

Every Friday at 5 PM, this workflow:

1. **Fetches** commits, merged PRs, and closed issues from your GitHub repo (past 7 days)
2. **Aggregates** data into a structured summary (top contributors, PR titles, issue list)
3. **Generates** a narrative summary via Claude Sonnet 4 API
4. **Delivers** the summary to your Discord/Slack channel

## Setup (5 Steps)

### 1. Prerequisites
- n8n instance (cloud or self-hosted)
- GitHub Personal Access Token with `repo` scope
- Claude API key (from [console.anthropic.com](https://console.anthropic.com))
- Discord webhook URL OR Slack webhook URL

### 2. Import the Workflow
1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `n8n_weekly_dev_summary.json`

### 3. Configure Credentials
In n8n, create these credentials:

| Credential Name | Type | What to Enter |
|:----------------|:-----|:--------------|
| `github-credentials` | HTTP Header Auth | Header: `Authorization`, Value: `Bearer YOUR_GITHUB_TOKEN` |
| `claude-credentials` | HTTP Header Auth | Header: `x-api-key`, Value: `YOUR_CLAUDE_API_KEY` |

### 4. Set Configuration Variables
Edit the **Set Config** node with your values:

| Variable | Example | Description |
|:---------|:--------|:------------|
| `repoUrl` | `https://api.github.com/repos/owner/repo` | Your GitHub repo API URL |
| `repoName` | `owner/repo` | Display name for the summary |
| `webhookUrl` | `https://discord.com/api/webhooks/...` | Discord or Slack webhook URL |
| `language` | `EN` | Output language (`EN` or `FR`) |

### 5. Activate the Workflow
1. Click **Save**
2. Toggle **Active** to ON
3. Test with **Execute Workflow** button

## Output Example

```
📊 Weekly Dev Summary - owner/repo

📈 Executive Summary
This week saw 23 commits across the repository, with 5 pull requests merged 
and 8 issues closed. The team focused heavily on performance optimization 
and bug fixes, with notable improvements to the authentication system.

🏆 Top Contributors
- Alice (8 commits) — API rate limiting improvements
- Bob (6 commits) — Database migration fixes
- Carol (5 commits) — Frontend test suite expansion

🔀 Merged PRs
- fix: handle edge case in auth token refresh (#142)
- feat: add request timeout configuration (#138)
- chore: update dependencies to latest versions (#136)

🔧 Issues Closed
- Critical: Memory leak in WebSocket connections (#89)
- Bug: Pagination offset incorrect on user list (#87)

📅 Next Week
Planned work includes GraphQL API migration and load testing.
```

## Customization

- **Cron schedule**: Edit the Schedule Trigger node (default: Friday 5 PM)
- **Language**: Set `language` to `EN` (English) or `FR` (French)
- **Output format**: Modify the Discord/Slack webhook payload in the final node

## Troubleshooting

| Issue | Fix |
|:------|:----|
| "401 Unauthorized" on GitHub calls | Check your GitHub token has `repo` scope |
| Claude API returns 429 | Ensure your API key has sufficient quota |
| Empty summary | The repo may have no activity in the past 7 days |
| Webhook delivery fails | Verify the webhook URL is correct and the channel exists |

## License

MIT
