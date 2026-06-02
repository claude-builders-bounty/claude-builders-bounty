# n8n Weekly GitHub Summary Workflow

Automatically generate and post a weekly GitHub activity summary to Discord, powered by Claude AI.

## ⚡ Quick Setup (5 Steps)

### 1. Import the Workflow
1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `n8n-weekly-summary.json`
4. Click **Save** to keep a copy

### 2. Configure Credentials
Set up these credentials in n8n (**Credentials** → **New**):

| Credential | Type | Details |
|-----------|------|---------|
| **GitHub API** | OAuth2 or Personal Access Token | `repo` scope for private repos, `public_repo` for public |
| **Discord Webhook** | (no credential needed — paste URL directly) | Create at Server Settings → Integrations → Webhooks |
| **Claude API Key** | Header Auth | Key: `x-api-key`, Value: your Anthropic API key |

### 3. Set Your Variables
In the **Config** node, update these default values:

```javascript
// Change these values in the Config node
"repo": "owner/repo"          // → your actual repo, e.g. "n8n-io/n8n"
"discordWebhook": "..."       // → your Discord webhook URL
"language": "EN"              // → "EN" | "FR" | "ZH"
"claudeApiKey": "sk-ant-..." // → your Anthropic API key
```

> 💡 **Tip:** You can also pass these values dynamically via n8n's webhook trigger or manual execution with a JSON payload.

### 4. Activate the Schedule
1. Click the **Schedule Trigger** node
2. Switch **Activate** to ON (☑️)
3. The workflow runs automatically every **Friday at 17:00** (your server timezone)

### 5. Test & Verify
1. Click **Execute Workflow** (play button) to run a manual test
2. Check your Discord channel for the summary message
3. Verify the Claude-generated narrative looks correct

---

## 🔧 Configuration Reference

### Schedule
- **Default**: Every Friday at 17:00 — cron `0 17 * * 5`
- **Customize**: Edit the **Schedule Trigger** node → change the cron expression

### Supported Languages
| Code | Language |
|------|----------|
| `EN` | English (default) |
| `FR` | French |
| `ZH` | Chinese |

### Claude Model
- **Default**: `claude-sonnet-4-20250514` (Sonnet 4)
- To change, update the `claudeModel` variable in the **Config** node

### GitHub API Rate Limits
- Unauthenticated: 60 req/hour (not recommended)
- Authenticated: 5,000 req/hour (use a personal access token)

---

## 📦 What It Does

Every Friday, this workflow:
1. 📅 Calculates the past 7 days
2. 🔍 Fetches from GitHub API:
   - All commits
   - Closed issues
   - Merged pull requests
3. 🤖 Sends data to **Claude Sonnet 4** to generate a narrative summary
4. 📬 Posts the summary to Discord as a rich embed with:
   - Activity stats (commits, issues, PRs)
   - Top contributors
   - AI-generated highlights

---

## 📄 License

MIT — built for the Opire bounty ([claude-builders-bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)).
