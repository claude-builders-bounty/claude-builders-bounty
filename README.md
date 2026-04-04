# n8n Weekly Dev Summary with Claude

Automated weekly development summary generation using n8n and Claude API.

## 🎯 What This Does

This n8n workflow automatically generates a narrative summary of your GitHub repository's weekly activity and delivers it to Discord or Slack.

### Features
- ✅ Weekly cron trigger (Friday 5 PM)
- ✅ Fetches GitHub data: commits, closed issues, merged PRs
- ✅ Claude API integration (claude-sonnet-4-20250514)
- ✅ Discord/Slack webhook delivery
- ✅ Configurable variables: repo, language, webhook

## ⚡ Quick Setup (5 Steps)

### 1. Import Workflow
```bash
# In n8n UI
Settings → Import Workflow → Upload weekly-dev-summary.json
```

### 2. Configure GitHub API Token
```bash
# Create GitHub Personal Access Token
# https://github.com/settings/tokens

# In n8n
Credentials → Add Credential → HTTP Header Auth
- Name: GitHub API Token
- Header: Authorization
- Value: token YOUR_GITHUB_TOKEN
```

### 3. Add Claude API Key
```bash
# Get Claude API Key
# https://console.anthropic.com/

# In n8n
Credentials → Add Credential → HTTP Header Auth
- Name: Claude API Key
- Header: x-api-key
- Value: YOUR_CLAUDE_API_KEY
```

### 4. Set Environment Variables
```bash
# In n8n
Settings → Variables → Add Variables

GITHUB_REPO=owner/repo
LANGUAGE=EN
WEBHOOK_URL=https://discord.com/api/webhooks/ID/TOKEN
```

### 5. Activate Workflow
```bash
# In n8n
Open workflow → Toggle "Active" switch (top right)
```

## 🎨 Customization

### Change Schedule
```javascript
// In Cron Trigger node
"0 17 * * 5"  // Friday 5 PM
"0 9 * * 1"   // Monday 9 AM
```

### Change Language
```bash
LANGUAGE=FR  # French
LANGUAGE=EN  # English
```

### Change Webhook URL
```bash
# Discord
WEBHOOK_URL=https://discord.com/api/webhooks/ID/TOKEN

# Slack
WEBHOOK_URL=https://hooks.slack.com/services/T000/B000/XXXX
```

## 📊 Example Output

```
📊 Weekly Dev Summary - April 4, 2026

Introduction:
This week saw 23 commits, 5 closed issues, and 3 merged PRs.

Highlights:
- Added new concurrent rendering feature
- Fixed memory leak in useEffect cleanup
- Improved TypeScript type inference

Top Contributors:
- @gaearon (8 commits)
- @sebmarkbage (5 commits)

Suggested Next Steps:
- Review open RFCs for new features
- Consider performance optimization
- Update documentation
```

## 🧪 Testing

### Manual Test
```bash
# In n8n UI
Open workflow → Execute Workflow
```

### Expected Results
1. ✅ GitHub API returns data successfully
2. ✅ Claude API generates narrative summary
3. ✅ Webhook delivers message to Discord/Slack

## 🔧 Requirements

- n8n version 1.0+
- GitHub Personal Access Token (repo scope)
- Claude API key
- Discord or Slack webhook URL

## 📝 Notes

- Workflow uses environment variables for easy configuration
- Supports both Discord and Slack webhooks (same payload format)
- Claude model: claude-sonnet-4-20250514 (Sonnet 4)
- Rate limit handling included in GitHub API calls

## 🎫 Bounty

- **Issue**: #5
- **Reward**: $200 USDT
- **Repository**: [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty)

## 📄 License

MIT License - Feel free to modify and distribute

---

**Author**: 小米粒 (Xiaomili) 🌾
**Date**: 2026-04-04
