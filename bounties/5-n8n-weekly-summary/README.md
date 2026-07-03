# n8n + Claude Code - Weekly Dev Summary Workflow

**Bounty #5 - $200**

An automated n8n workflow that generates a weekly development summary from GitHub activity and posts it as an issue.

## How It Works

1. **Schedule Trigger** - Runs every Monday at 9:00 AM
2. **Fetch PRs** - Gets all merged PRs from the past 7 days via GitHub API
3. **Filter** - Keeps only PRs merged in the last week
4. **Code Node (Summary Gen)** - Categorizes PRs (features/fixes/docs/refactors/tests) and builds a markdown report
5. **GitHub Issue Creator** - Posts the summary as a new issue with `weekly-summary` label

## Files

| File | Description |
|------|-------------|
| `weekly-dev-summary.json` | n8n workflow (import into n8n) |
| `README.md` | This file |

## Import into n8n

1. Open your n8n instance
2. Go to **Workflows** ? **Import from File**
3. Select `weekly-dev-summary.json`
4. Configure the **GitHub credential** node with your token
5. Set the `repository_url` parameter to your repo
6. Activate the workflow

## Customization

- Change the cron schedule in the Schedule Trigger node
- Modify the Code node to change the report format
- Add Slack/Email notification nodes for alerts

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub API token with `repo` scope
