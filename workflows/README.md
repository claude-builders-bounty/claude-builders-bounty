# n8n Weekly Dev Summary Workflow

Automated weekly development summary using n8n + Claude API.

## 🚀 Setup (5 Steps)

### 1. Import Workflow
- Open n8n → Workflows → Import from File
- Select `n8n-weekly-dev-summary.json`

### 2. Configure Credentials
Set these environment variables in n8n:

```bash
# GitHub
GITHUB_OWNER=your-org
GITHUB_REPO=your-repo
GITHUB_TOKEN=ghp_xxx

# Claude API
ANTHROPIC_API_KEY=sk-ant-xxx

# Delivery (choose one or both)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SLACK_CHANNEL=#dev-updates

# Language
LANGUAGE=EN  # or FR
```

### 3. Set Schedule
- Edit "Weekly Cron" node
- Default: Every Friday at 5 PM
- Customize as needed

### 4. Test
- Click "Execute Workflow"
- Check output in Discord/Slack

### 5. Activate
- Toggle workflow to "Active"
- Done! 🎉

## 📊 What It Does

1. **Triggers** weekly via cron
2. **Fetches** commits, closed issues, merged PRs from GitHub
3. **Generates** narrative summary via Claude API
4. **Delivers** to Discord or Slack

## 📝 Example Output

```
📊 Weekly Dev Summary (Apr 1-7)

📝 Commits: 15
✅ Closed Issues: 8
🔀 Merged PRs: 5

Highlights:
- Fixed critical auth bug (#123)
- Launched new dashboard feature
- Improved API response times by 40%
```

## 🔧 Requirements

- n8n instance (cloud or self-hosted)
- GitHub Personal Access Token
- Anthropic API Key
- Discord webhook OR Slack bot token

## 💰 Bounty

This workflow was created for [claude-builders-bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)