# Setup Guide: n8n Weekly Dev Summary

## Prerequisites
- n8n instance (cloud or self-hosted)
- GitHub Personal Access Token (repo scope)
- Anthropic API key (for Claude)
- Slack Bot Token (chat:write scope)

## Configuration

### 1. Environment Variables
Set these in n8n → Settings → Environment Variables:
```
GITHUB_REPO=owner/repo
SLACK_CHANNEL=#dev-updates
```

### 2. Credentials
Add in n8n → Credentials:
- **HTTP Header Auth** (for GitHub): Header `Authorization`, Value `Bearer ghp_xxx`
- **Anthropic API**: API key for Claude
- **Slack**: Bot User OAuth Token

### 3. Import Workflow
1. Download `workflow.json`
2. n8n → Workflows → Import from File
3. Configure credentials on each node

### 4. Test
Click "Execute Workflow" to test with current data before the scheduled run.

## Customization
- Change cron expression in the trigger node for different schedule
- Modify the Claude prompt for different summary formats
- Replace Slack with Discord/Email by swapping the last node
