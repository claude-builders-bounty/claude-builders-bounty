# Weekly Dev Summary — n8n Workflow

Automatically generates a weekly narrative summary of a GitHub repo's activity using Claude API.

## Setup (5 Steps)

1. **Import the workflow**: In n8n, go to **Workflows → Add Workflow → Import from File** and select `workflow.json`

2. **Set environment variables** in n8n:
   - `GITHUB_TOKEN` — GitHub personal access token with `repo` scope
   - `CLAUDE_API_KEY` — Anthropic API key
   - `WEBHOOK_URL` — Discord/Slack webhook URL for delivery

3. **Configure repo** (optional): Edit the "Set Config" node to set `repoOwner` and `repoName` for your repo

4. **Set language** (optional): Change `language` in "Set Config" to `EN` or `FR`

5. **Activate**: Click **Active** toggle to start. Workflow runs every Friday at 5pm UTC.

## How It Works

| Node | Purpose |
|------|---------|
| Weekly Schedule | Cron trigger (Fri 5pm UTC), configurable |
| Set Config | Repo owner, name, language, webhook URL |
| Get Commits | Fetches commits via GitHub API (paginated) |
| Get Closed Issues | Fetches closed issues for the week |
| Get Merged PRs | Fetches merged PRs for the week |
| Merge Activity | Combines all data into one stream |
| Build Prompt | Constructs structured prompt with stats + instructions |
| Claude API | Calls claude-sonnet-4-20250514 to generate narrative |
| Extract Summary | Parses Claude response into clean summary |
| Send to Webhook | Delivers to Discord/Slack via webhook |

## Customization

- **Change schedule**: Edit the "Weekly Schedule" node's cron expression
- **Add email delivery**: Replace or chain after "Send to Webhook" with n8n's Email node
- **Add Slack**: Use n8n's Slack node instead of generic webhook

## Requirements

- n8n (self-hosted or cloud)
- GitHub API token (free)
- Claude API key (Anthropic)
- Discord/Slack webhook URL

## Testing

To test, manually execute the workflow in n8n by clicking "Execute Workflow". Check the output of the "Send to Webhook" node for the delivered summary.
