# GitHub Weekly Summary - n8n Workflow

An n8n workflow that automatically generates weekly narrative summaries of GitHub repository activity using the Claude API.

## Features

- **Automated Trigger**: Runs every Friday at 5 PM (configurable)
- **Data Collection**: Fetches commits, closed issues, and merged PRs from the past week
- **AI Summary**: Uses Claude API to generate a narrative summary
- **Delivery**: Sends to Discord/Slack webhook (configurable)
- **Multi-language**: Supports EN/FR output

## Setup (5 Steps)

### 1. Import Workflow
```bash
# In n8n, go to Workflows → Import from File
# Select github-weekly-summary.json
```

### 2. Configure Credentials
Add two credentials in n8n:
- **GitHub Token**: HTTP Header Auth with `Authorization: Bearer YOUR_GITHUB_TOKEN`
- **Claude API**: Anthropic API key

### 3. Set Environment Variables
```bash
GITHUB_REPO=owner/repository
GITHUB_API_URL=https://api.github.com  # or your GitHub Enterprise URL
WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy  # or Slack webhook
LANGUAGE=EN  # or FR
```

### 4. Activate Workflow
Click "Activate" in n8n to enable the scheduled trigger.

### 5. Test Execution
Click "Execute Workflow" to test with current data.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_REPO` | Target repository (owner/repo) | Required |
| `GITHUB_API_URL` | GitHub API endpoint | `https://api.github.com` |
| `WEBHOOK_URL` | Discord/Slack webhook URL | Required |
| `LANGUAGE` | Output language | `EN` |

## Workflow Nodes

1. **Weekly Trigger** - Cron: `0 17 * * 5` (Friday 5 PM)
2. **Get Commits** - Fetches commits from past 7 days
3. **Get Closed Issues** - Fetches closed issues from past 7 days
4. **Get Merged PRs** - Fetches merged PRs from past 7 days
5. **Merge Data** - Combines all GitHub data
6. **Claude Summary** - Generates narrative using `claude-sonnet-4-20250514`
7. **Format Output** - Converts to Markdown
8. **Send Webhook** - Delivers to Discord/Slack

## Output Example

```markdown
# Weekly Summary for owner/repository

This week, the team made significant progress on the new feature release.
Key highlights include:

- 15 commits focusing on performance improvements
- 5 closed issues, including the critical bug #123
- 3 merged PRs adding new API endpoints

The main contributor this week was @developer with 10 commits.
---
_Generated on 2026-04-09_
```

## Testing

To test manually without waiting for the scheduled trigger:
1. Open the workflow in n8n
2. Click "Execute Workflow"
3. Check the output of each node

## Requirements

- n8n instance (self-hosted or n8n.cloud)
- GitHub Personal Access Token (with `repo` scope)
- Anthropic API key
- Discord or Slack webhook URL

## Bounty

Created for [$200 Bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5).

## License

MIT
