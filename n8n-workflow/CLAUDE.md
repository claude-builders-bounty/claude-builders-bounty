# n8n Workflow

This is an n8n workflow for generating weekly development summaries using Claude API.

## Files

- `workflow.json` - n8n workflow export (import in n8n)
- `README.md` - Setup instructions

## Setup

1. Import `workflow.json` into n8n
2. Set variables: GITHUB_REPO, DISCORD_WEBHOOK_URL
3. Add API credentials
4. Activate workflow

## Output

Weekly GitHub activity summary sent to Discord.