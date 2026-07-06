# GitHub Weekly Summary with Claude API

Automatically generate narrative summaries of your GitHub repository's weekly activity using Claude AI.

## 🎯 Features

- ✅ Weekly cron trigger (configurable day/time)
- ✅ Fetches commits, closed issues, and merged PRs from GitHub API
- ✅ Generates natural language summaries using Claude Sonnet 4
- ✅ Multi-language support (English/French)
- ✅ Multiple delivery methods: Email (SendGrid), Slack, or Discord
- ✅ Fully configurable via environment variables

## 📋 Quick Setup (5 Steps)

### Step 1: Import the Workflow
1. Open your n8n instance
2. Click **Workflows** → **Create new**
3. Click **Import** → paste `n8n_github_summary_workflow.json`
4. Click **Import workflow**

### Step 2: Set Up Credentials
In n8n, create these credentials in **Settings → Credentials**:

| Credential | Type | Setup |
|-----------|------|-------|
| **GitHub API Token** | HTTP Basic Auth | Username: `x-access-token`, Password: `[GitHub PAT]` |

Get a GitHub PAT: https://github.com/settings/tokens/new (scopes: `repo`, `read:user`)

### Step 3: Configure Environment Variables
Set these in your n8n `.env` file or n8n UI (**Settings → Environment Variables**):

```
GITHUB_API_TOKEN=ghp_xxxxx...
GITHUB_REPO=owner/repo_name
CLAUDE_API_KEY=sk-ant-xxxxx...
SUMMARY_LANGUAGE=EN
DELIVERY_METHOD=slack|email|discord
SLACK_WEBHOOK=https://hooks.slack.com/services/...
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
EMAIL_TO=your-email@example.com
FROM_EMAIL=notifications@yourdomain.com
SENDGRID_API_KEY=SG.xxxxx...
```

### Step 4: Configure Delivery Method
Choose one of these:

**Email (SendGrid):**
- Set `DELIVERY_METHOD=email`
- Create SendGrid account: https://sendgrid.com
- Get API key from SendGrid Dashboard
- Set `SENDGRID_API_KEY` and `EMAIL_TO`

**Slack:**
- Set `DELIVERY_METHOD=slack`
- Create incoming webhook: https://api.slack.com/apps
- Set `SLACK_WEBHOOK` to the webhook URL

**Discord:**
- Set `DELIVERY_METHOD=discord`
- Create webhook in Discord server settings (Server → Integrations → Webhooks)
- Set `DISCORD_WEBHOOK` to the webhook URL

### Step 5: Activate & Test
1. Click **Activate** in the workflow editor
2. Click **Manual Test** to trigger immediately
3. Check your delivery method (email/Slack/Discord) for the summary
4. The workflow will now run weekly on Friday at 5pm UTC

## 🔧 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_API_TOKEN` | ✅ | — | GitHub Personal Access Token |
| `GITHUB_REPO` | ❌ | `claude-builders-bounty/claude-builders-bounty` | Repository (format: `owner/repo`) |
| `CLAUDE_API_KEY` | ✅ | — | Anthropic API Key |
| `SUMMARY_LANGUAGE` | ❌ | `EN` | Output language: `EN` or `FR` |
| `DELIVERY_METHOD` | ❌ | `slack` | Delivery: `email`, `slack`, or `discord` |
| `SLACK_WEBHOOK` | ❌ | — | Slack incoming webhook URL |
| `DISCORD_WEBHOOK` | ❌ | — | Discord webhook URL |
| `EMAIL_TO` | ❌ | — | Email recipient address |
| `FROM_EMAIL` | ❌ | `noreply@example.com` | Sender email address |
| `SENDGRID_API_KEY` | ❌ | — | SendGrid API key for email delivery |

## 📊 Sample Output

```
Weekly Summary - claude-builders-bounty/claude-builders-bounty

This week brought significant progress to the repository with 23 commits, 
12 closed issues, and 8 merged pull requests. Key highlights include:

The team focused on API integration improvements, with notable work in 
authentication flows and error handling. Several performance optimizations 
were merged, reducing latency in core workflows.

Community engagement remained strong with contributors closing multiple 
enhancement requests and bug reports. The codebase is in a stable state 
with all CI checks passing.
```

## 🧪 Testing

### Manual Trigger
1. Open the workflow → Click **Manual Test**
2. Check execution logs in the **Executions** tab
3. Verify summary arrives in your delivery channel within 30 seconds

### Debug Logs
- Click workflow → **Execution Details** tab
- Review request/response for each node
- Check HTTP status codes (should be 200/201)

### Common Issues

| Issue | Solution |
|-------|----------|
| GitHub API returns 401 | Verify `GITHUB_API_TOKEN` is valid and has `repo` scope |
| Claude API returns 401 | Check `CLAUDE_API_KEY` is correct |
| Slack delivery fails | Paste webhook URL directly in n8n UI, verify channel permissions |
| No data fetched | Ensure `GITHUB_REPO` format is `owner/repo` with matching case |

## 📈 Customization

### Change Schedule
Edit the **Weekly Trigger** node:
- **Interval Unit**: days/weeks/months
- **Trigger At Hour**: 0-23
- **Trigger At Minute**: 0-59
- **Trigger At Day**: 0 (Sunday) - 6 (Saturday)

### Adjust Summary Length
In the **Generate Summary with Claude** node, change `max_tokens`:
- `512` = brief summary
- `1024` = standard (current)
- `2048` = detailed

### Add More GitHub Data
Extend the **Parse GitHub Data** node to include:
- Releases: `GET /repos/{owner}/{repo}/releases`
- Contributors: `GET /repos/{owner}/{repo}/contributors`
- Stars: `GET /repos/{owner}/{repo}/stargazers`

## 🚀 Deployment

### Docker Compose
```yaml
version: '3'
services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      GITHUB_API_TOKEN: ${GITHUB_API_TOKEN}
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
      SLACK_WEBHOOK: ${SLACK_WEBHOOK}
    volumes:
      - n8n_data:/home/node/.n8n
```

Run: `docker-compose up -d`

### Cloud Hosting
- **n8n Cloud**: https://n8n.cloud (managed)
- **Railway**: https://railway.app
- **Render**: https://render.com

## 📞 Support

- n8n Docs: https://docs.n8n.io
- Claude API: https://docs.anthropic.com
- GitHub API: https://docs.github.com/en/rest

## 📄 License

This workflow is provided as-is under the MIT License.

---

**Bounty:** $200 USD
**Status:** Ready for production
**Last Updated:** 2026-07-06
