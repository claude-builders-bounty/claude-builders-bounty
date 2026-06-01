# n8n + Claude API — Weekly Dev Summary

Automated workflow that generates a narrative weekly summary of GitHub repo activity using Claude API.

## Setup (5 steps)

1. **Install n8n**
   ```bash
   npm install -g n8n
   n8n start
   ```

2. **Import workflow**
   - Open n8n at http://localhost:5678
   - Settings → Import from File → select `weekly-dev-summary.json`

3. **Set environment variables**
   ```bash
   export CLAUDE_API_KEY="sk-ant-..."
   ```

4. **Configure variables** (in n8n Workflow Static Data)
   - `github_repo`: owner/repo (e.g., `claude-builders-bounty/claude-builders-bounty`)
   - `webhook_url`: Discord/Slack webhook URL
   - `language`: EN or FR

5. **Activate workflow**
   - Toggle "Active" switch in n8n
   - Workflow runs every Friday at 5pm

## Architecture

```
Weekly Cron → Compute Dates → Fetch Commits/Issues/PRs → Aggregate → Claude API → Deliver
```

## Customization

- **Email delivery**: Replace last node with `n8n-nodes-base.emailSend`
- **Language**: Set `language` to `FR` for French summaries
- **Schedule**: Edit cron expression in `Weekly Cron` node

## Test Run

Click "Test workflow" in n8n to execute manually and verify output.
