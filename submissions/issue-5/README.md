# Weekly Dev Summary with Claude - n8n Workflow

An automated n8n workflow that generates weekly narrative summaries of GitHub repository activity using Claude API (claude-sonnet-4-20250514) and delivers them to Discord or Slack.

## Features

- ✅ Weekly automated trigger (Fridays at 5 PM)
- ✅ Fetches commits, closed issues, and merged PRs from GitHub API
- ✅ Generates narrative summary using Claude API
- ✅ Delivers to Discord or Slack via webhooks
- ✅ Configurable repository, language (EN/FR), and destination
- ✅ Built-in pagination support for GitHub API
- ✅ Error handling included

## Required API Keys

Before setting up this workflow, you'll need:

1. **GitHub Personal Access Token**
   - Go to: https://github.com/settings/tokens
   - Create token with `repo` scope (read access to repositories)
   - Copy the token

2. **Anthropic API Key (Claude)**
   - Go to: https://console.anthropic.com/
   - Create an API key
   - Copy the key

3. **Discord Webhook URL** (optional - for Discord delivery)
   - In your Discord server: Server Settings → Integrations → Webhooks
   - Create a new webhook for your desired channel
   - Copy the webhook URL

4. **Slack Webhook URL** (optional - for Slack delivery)
   - Go to: https://api.slack.com/apps
   - Create incoming webhook
   - Copy the webhook URL

## 5-Step Setup Instructions

### Step 1: Import Workflow into n8n

1. Open your n8n instance
2. Click the **+** button to create a new workflow
3. Click the **⋮** menu (three dots) in the top right
4. Select **Import from File**
5. Choose `n8n-weekly-dev-summary.json`
6. Click **Import**

### Step 2: Configure Environment Variables

In your n8n instance, set the following environment variables:

```bash
# Required
GITHUB_REPO=owner/repository           # e.g., "facebook/react"
LANGUAGE=EN                             # "EN" for English, "FR" for French
WEBHOOK_TYPE=discord                    # "discord" or "slack"

# Choose ONE of the following based on WEBHOOK_TYPE:
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
# OR
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

**For n8n cloud**: Go to Settings → Variables  
**For self-hosted**: Add to your `.env` file or docker-compose environment

### Step 3: Add Credentials

1. In the workflow, click on **"Get Commits"** node
2. Under **Credentials**, click **Create New**
3. Select **Header Auth**
4. Configure:
   - **Name**: `GitHub API Token`
   - **Header Name**: `Authorization`
   - **Header Value**: `Bearer YOUR_GITHUB_TOKEN_HERE`
5. Click **Save**

6. Repeat for **"Generate Summary with Claude"** node:
   - **Name**: `Claude API Key`
   - **Header Name**: `x-api-key`
   - **Header Value**: `YOUR_ANTHROPIC_API_KEY_HERE`
7. Click **Save**

### Step 4: Customize Schedule (Optional)

By default, the workflow runs every **Friday at 5 PM**. To change:

1. Click on **"Weekly Trigger (Friday 5PM)"** node
2. Modify the cron expression:
   - `0 17 * * 5` = Friday at 5 PM
   - `0 9 * * 1` = Monday at 9 AM
   - `0 12 * * *` = Every day at noon

### Step 5: Test and Activate

1. Click **Test Workflow** button (top right) to run a manual test
2. Check the execution to ensure:
   - GitHub API returns data
   - Claude generates a summary
   - Webhook delivers the message
3. If successful, click **Activate** toggle (top right)
4. Your workflow will now run automatically on schedule!

## Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_REPO` | GitHub repository in format `owner/repo` | - | ✅ |
| `LANGUAGE` | Summary language (`EN` or `FR`) | `EN` | ❌ |
| `WEBHOOK_TYPE` | Destination type (`discord` or `slack`) | - | ✅ |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | - | If using Discord |
| `SLACK_WEBHOOK_URL` | Slack webhook URL | - | If using Slack |

## Example Output

### Discord/Slack Message:

```markdown
📊 Weekly Dev Summary - facebook/react

Week Ending: 2025-04-04

---

# Weekly Development Summary

This was an active week for the facebook/react repository! Here's what happened:

## Commits (47 total)
The team made significant progress with several performance improvements and bug fixes. Notable commits include:
- "Optimize reconciliation algorithm" by Sophie
- "Fix memory leak in useEffect cleanup" by Dan
- "Update TypeScript definitions" by Sebastian

## Closed Issues (12 total)
We successfully resolved 12 issues this week, including:
- #24892: Memory leak with concurrent rendering
- #24887: TypeScript type inference issues
- #24881: Warning flooding in development mode

## Merged Pull Requests (8 total)
The community contributed 8 merged PRs:
- #24895: Add benchmarks for new features (by contributor123)
- #24890: Improve error boundaries (by reactfan42)

Overall, it's been a productive week with steady progress on stability and performance improvements!
```

## Troubleshooting

### "No data returned from GitHub"
- Verify your GitHub token has `repo` scope
- Check that `GITHUB_REPO` is in format `owner/repo`
- Ensure the repository exists and is accessible

### "Claude API error"
- Verify your Anthropic API key is valid
- Check your API usage limits at https://console.anthropic.com/

### "Webhook delivery failed"
- Test your webhook URL with curl:
  ```bash
  curl -X POST YOUR_WEBHOOK_URL \
    -H "Content-Type: application/json" \
    -d '{"content":"Test message"}'
  ```
- Ensure `WEBHOOK_TYPE` matches your webhook type

## License

MIT License - Feel free to modify and distribute!

## Support

For issues or feature requests, please open an issue in the repository.

---

**Created for**: Claude Builders Bounty - Issue #5  
**Workflow Version**: 1.0.0
