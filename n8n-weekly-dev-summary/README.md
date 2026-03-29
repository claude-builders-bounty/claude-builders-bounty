# n8n Weekly Dev Summary

An n8n workflow that generates a weekly narrative summary of GitHub repo activity using the Claude API. Delivers via Discord webhook or email.

 

## Setup (4 steps)

1. **Import the workflow**
   ```
   n8n import:workflow --input=weekly-dev-summary.json
   ```

2. **Create credentials in n8n**
   - **GitHub Token**: Header Auth credential, header name `Authorization`, value `Bearer ghp_xxxxx`
   - **Anthropic API Key**: Header Auth credential, header name `x-api-key`, value `sk-ant-xxxxx`

3. **Configure variables** in the workflow settings:

| Variable | Example | Required |
|----------|---------|----------|
| `GITHUB_REPO` | `owner/repo` | ✅ |
| `LANGUAGE` | `EN` or `FR` | No (default: EN) |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | One delivery channel |
| | `EMAIL_FROM` | noreply@devsummary.com | One delivery channel |
| | `EMAIL_TO` | team@example.com | One delivery channel |

4. **Activate** the workflow in n8n, click the toggle. Run manually to test.

 

## How it works

```
Trigger (Friday 5pm) → GitHub API (commits, issues, PRs) → Aggregate → Build Prompt → Claude API → Format → Discord + Email
```

 

## Sample Output

```markdown
Weekly Dev Summary: owner/repo

This week saw 23 commits, 5 issues closed, and 3 PRs merged. The team shipped a new
 authentication middleware (PR #142) while Sarah refactored the database query builder for a 40% performance gain. The auth module now uses JWT-based token rotation with 10 new anti-patterns to the codebase. The next step is OAuth integration and E2E testing improvements. 

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_REPO` | Target repo (owner/repo) | *(required)* |
| `LANGUAGE` | Output language (`EN` or `FR`) | `EN` |
| `DISCORD_WEBHOOK_URL` | Discord webhook in `https://discord.com/api/webhooks/...` | *(optional)* |
| `EMAIL_FROM` | Sender address | *(optional)* |
| `EMAIL_TO` | Recipient address | *(optional)* |

## Requirements

- n8n (v1.66.0+)
 - GitHub Personal Access Token
 - Anthropic API key

## License

MIT
