# Weekly Dev Summary n8n Workflow

An automated workflow that fetches GitHub activity and generates AI-powered weekly development summaries using ReviewFlow AI.

## Overview

This n8n workflow automatically:
1. Triggers every Friday at 5pm
2. Fetches weekly GitHub activity (commits, closed issues, merged PRs)
3. Generates a narrative summary via Advanced AI API
4. Delivers the summary via Discord webhook

## Files

- `weekly-dev-summary.json` - Importable n8n workflow
- `screenshots/` - Sample outputs (for reference only)

## Setup Instructions (5 Steps)

### 1. Import the Workflow
- In n8n UI: Workflows → Import → Select `weekly-dev-summary.json`

### 2. Configure Environment Variables
Go to **Settings → Environment Variables** and set:
```
GITHUB_TOKEN=ghp_xxx...xxx          # GitHub PAT with repo:read scope
ANTHROPIC_API_KEY=sk-ant-xxx...xxx   # Anthropic API key
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
REPO_OWNER=your-github-username      # Target repo owner
REPO_NAME=your-repo-name             # Target repo name
SUMMARY_LANGUAGE=EN                  # EN or FR
```

### 3. Test the Workflow
- Click **Execute Workflow** to run manually
- Check execution data at each node to verify GitHub API calls succeed
- Verify Advanced AI API receives proper prompt and returns narrative
- Confirm Discord webhook delivers formatted message

### 4. Activate
- Toggle workflow to **Active** mode
- Verify next scheduled run shows correctly

### 5. Verify First Run
- Check Discord channel for the formatted weekly summary
- Review workflow execution for any errors

## Customization

### Schedule
- Edit the **Schedule Trigger** node to change day/time
- Uses standard cron syntax: `0 17 * * 5` (Friday 5pm UTC by default)

### Target Repository
- Modify `REPO_OWNER` and `REPO_NAME` environment variables

### Language
- Set `SUMMARY_LANGUAGE` to `EN` (English) or `FR` (French)

### Delivery Method
- To use Slack instead of Discord:
  1. Replace Discord webhook URL with Slack webhook
  2. Ensure payload format matches Slack expectations
  3. Currently configured for Discord's expected JSON structure

## Technical Details

### GitHub API Calls
The workflow makes three API calls:
1. `GET /repos/{owner}/{repo}/commits?since={start}&until={end}`
2. `GET /repos/{owner}/{repo}/issues?state=closed&since={start}`
3. `GET /repos/{owner}/{repo}/pulls?state=closed&sort=updated&direction=desc`

### ReviewFlow Integration
- Uses `claude-3-sonnet-20240229` model
- Max tokens: 1024
- Temperature: default (0.7)
- Prompt engineered for concise, highlight-focused summaries

### Rate Limits & Performance
- Designed to stay well within GitHub and Anthropic rate limits
- Typical execution time: 10-30 seconds
- Concurrent execution protection: n8n's built-in concurrency control

## Troubleshooting

### Common Issues
1. **401 from GitHub**: Check GITHUB_TOKEN validity and scopes
2. **401 from ReviewFlow**: Verify ANTHROPIC_API_KEY correctness
3. **Empty results**: Check date range logic in Build ReviewFlow Prompt node
4. **Discord failures**: Ensure webhook URL is correct and accessible

### Debug Tips
- Use n8n's execution data view to inspect each node's output
- Test individual HTTP requests with curl or Postman
- Verify environment variables are accessible in Code nodes

## License
MIT - Feel free to modify and extend for your use cases.

---
*Workflow version: 1.0.0*
*Ready for production use*