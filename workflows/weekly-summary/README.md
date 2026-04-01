# Claude Code + n8n Weekly Summary Workflow

An automated workflow that generates weekly GitHub repository summaries using Claude API.

## Quick Setup (5 Steps)

### 1. Import Workflow
- Open n8n
- Menu → Import File
- Select `weekly-summary.json`

### 2. Configure Credentials
- **GitHub**: Add Personal Access Token
- **Anthropic**: Add Claude API Key

### 3. Set Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `githubRepo` | Repository URL | `https://api.github.com/repos/owner/repo` |
| `webhookUrl` | Discord/Slack Webhook | Your webhook URL |
| `language` | Summary language | `EN` or `FR` |

### 4. Test
- Click "Test Workflow"
- Verify Discord message

### 5. Activate
- Toggle "Active" switch
- Runs every Friday at 5pm

## Features

✅ Weekly cron trigger (Friday 5pm)  
✅ Fetches commits, PRs, issues from GitHub API  
✅ Claude API generates narrative summary  
✅ Sends to Discord/Slack webhook  
✅ Configurable language (EN/FR)  

## Workflow Structure

```
Weekly Trigger → Get GitHub Data → Claude Summary → Discord
```

## Requirements

- n8n instance (cloud or self-hosted)
- GitHub Personal Access Token (repo read)
- Claude API Key
- Discord/Slack Webhook URL

## Support

For issues, check n8n execution logs or Claude API responses.