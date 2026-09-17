# n8n Weekly GitHub Dev Summary with Claude

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

## Features

- Weekly cron trigger (Friday at 5pm)
- Fetches commits, closed issues, and merged PRs from GitHub API
- Calls Claude API to generate a narrative summary
- Delivers via email AND/OR Discord webhook
- Configurable variables for repo, destination, and language

## Setup (5 steps or fewer)

### 1. Import the workflow

1. Open your n8n instance
2. Go to **Workflows** > **Import from File**
3. Select `workflow.json`

### 2. Set environment variables

In n8n, go to **Settings** > **Variables** and add:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Repository to monitor | `owner/repo-name` |
| `GITHUB_TOKEN` | GitHub personal access token | `ghp_xxxxx` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-xxxxx` |
| `NOTIFICATION_EMAIL` | Email for summaries | `team@example.com` |
| `DISCORD_WEBHOOK_URL` | Discord webhook (optional) | `https://discord.com/api/webhooks/xxx` |

### 3. Configure delivery

- **Email only**: Remove the "Send to Discord" node
- **Discord only**: Remove the "Send Email" node
- **Both**: Keep both nodes

### 4. Test the workflow

1. Click **Execute Workflow** in n8n
2. Check the execution logs for any errors
3. Verify you receive the summary

### 5. Activate the workflow

Toggle the workflow to **Active** to enable the weekly cron trigger.

## Configuration

### Change the schedule

Edit the "Weekly Cron Trigger" node:
- Default: Friday at 5pm (`0 17 * * 5`)
- Weekly Monday 9am: `0 9 * * 1`
- Daily at 6pm: `0 18 * * *`

### Change the language

Edit the Claude API prompt in the "Call Claude API" node to include:
```
Write the summary in French/Spanish/German/etc.
```

## Sample Output

```markdown
# Weekly Development Summary

## Overview
This week saw significant progress on the authentication system with 12 commits, 3 merged PRs, and 5 closed issues.

## Key Achievements
- **Auth System Complete**: The new OAuth2 authentication system has been fully implemented and tested
- **Performance Boost**: Database query optimization reduced response times by 40%
- **Bug Fixes**: Resolved critical issues with session management

## Notable Changes
- PR #142: Added Google OAuth2 provider
- PR #145: Implemented rate limiting
- PR #148: Fixed memory leak in WebSocket handler

## Team Contributions
- @alice: 5 commits, 2 PRs merged
- @bob: 4 commits, 1 PR merged
- @charlie: 3 commits, 3 issues closed

## Looking Ahead
Next week focuses on implementing the dashboard and setting up CI/CD pipeline.
```

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub account with personal access token
- Anthropic API key
- Email service configured (for email delivery)
- Discord webhook (for Discord delivery)

## Troubleshooting

### "Unauthorized" error from GitHub
- Ensure your GitHub token has `repo` scope
- Check the token hasn't expired

### "Invalid API key" error from Claude
- Verify your Anthropic API key is correct
- Check you have sufficient credits

### No email received
- Check your email service is configured in n8n
- Verify the `NOTIFICATION_EMAIL` variable is set

## License

MIT
