# Setup Instructions: GitHub Weekly Summary with Claude

## Overview
This workflow automatically generates narrative summaries of GitHub repository activity weekly using the Claude API, and delivers them via Slack, Discord, or Email.

---

## 5-Step Setup

### Step 1: Import Workflow into n8n
1. **Open your n8n instance** (https://app.n8n.cloud or self-hosted)
2. Click **Workflows** in the left sidebar
3. Click **Create new** → **Import workflow**
4. Copy the contents of `github_weekly_summary.json` and paste it
5. Click **Import** and give it a name

### Step 2: Get Required API Keys

**GitHub Personal Access Token:**
1. Go to https://github.com/settings/tokens/new
2. Click **Generate new token** → **Generate new token (classic)**
3. Set scopes:
   - ✅ `repo` (full control of private repositories)
   - ✅ `read:user` (read user profile data)
4. Copy the token (save it securely)

**Anthropic Claude API Key:**
1. Go to https://console.anthropic.com/
2. Click **API Keys** in the left sidebar
3. Click **Create Key**
4. Copy the key (starts with `sk-ant-`)

**Slack Webhook (Optional):**
1. Go to https://api.slack.com/apps
2. Click **Create New App** → **From scratch**
3. Name it "GitHub Summary Bot"
4. Go to **Incoming Webhooks** → **Add New Webhook to Workspace**
5. Select your channel and authorize
6. Copy the Webhook URL

**Discord Webhook (Optional):**
1. Right-click your Discord server → **Server Settings** → **Integrations** → **Webhooks**
2. Click **New Webhook**
3. Name it "GitHub Summary"
4. Copy the Webhook URL

**SendGrid API Key (Optional, for email):**
1. Go to https://sendgrid.com (create account if needed)
2. Navigate to **Settings** → **API Keys**
3. Click **Create API Key**
4. Copy the key (starts with `SG.`)

### Step 3: Set Environment Variables in n8n

Go to your n8n **Settings** → **Environment Variables** and add:

```
GITHUB_API_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_REPO=owner/repo
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxx
SUMMARY_LANGUAGE=EN
DELIVERY_METHOD=slack
SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

#### Required Variables:
- `GITHUB_API_TOKEN` - GitHub Personal Access Token
- `CLAUDE_API_KEY` - Anthropic API key

#### Optional/Configurable Variables:
- `GITHUB_REPO` - Repository (default: `claude-builders-bounty/claude-builders-bounty`)
- `SUMMARY_LANGUAGE` - `EN` or `FR` (default: `EN`)
- `DELIVERY_METHOD` - `slack`, `discord`, or `email` (default: `slack`)
- `SLACK_WEBHOOK` - Slack webhook URL (required if delivery_method=slack)
- `DISCORD_WEBHOOK` - Discord webhook URL (required if delivery_method=discord)
- `EMAIL_TO` - Email recipient (required if delivery_method=email)
- `FROM_EMAIL` - Sender email (default: `noreply@example.com`)
- `SENDGRID_API_KEY` - SendGrid API key (required if delivery_method=email)

### Step 4: Test the Workflow

1. **Open the workflow** in n8n editor
2. Click **Manual Test** (or **Test Workflow**)
3. Click **Execute Workflow**
4. Wait 10-30 seconds for execution
5. Check **Execution Details** tab to see logs

**Expected Result:**
- All nodes execute successfully (green checkmarks)
- Summary appears in your Slack channel / Discord server / Email inbox

### Step 5: Activate Workflow

1. Click **Activate** toggle in the top-right
2. Workflow now runs every Friday at 5:00 PM UTC
3. Check your delivery channel the following Friday

---

## Customization

### Change the Schedule
Edit **Weekly Trigger** node:
- **Interval Unit:** days / weeks / months
- **Trigger At Hour:** 0-23 (UTC)
- **Trigger At Minute:** 0-59
- **Trigger At Day:** 0 (Sun) - 6 (Sat)

### Change Repository
Update environment variable:
```
GITHUB_REPO=new-owner/new-repo
```

### Change Language
```
SUMMARY_LANGUAGE=FR
```

### Switch Delivery Method
```
DELIVERY_METHOD=email
# Then set EMAIL_TO, FROM_EMAIL, SENDGRID_API_KEY
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Workflow won't activate** | Check that all required API keys are set in Environment Variables |
| **GitHub returns 401** | Verify `GITHUB_API_TOKEN` is correct and hasn't expired |
| **Claude returns 401** | Check `CLAUDE_API_KEY` is valid (starts with `sk-ant-`) |
| **Slack message not sent** | Verify `SLACK_WEBHOOK` URL is correct; test webhook directly: `curl -X POST -d '{"text":"test"}' <WEBHOOK_URL>` |
| **No data fetched** | Check `GITHUB_REPO` format is exact (case-sensitive): `owner/repo` |
| **Workflow hangs** | Increase HTTP timeout in each HTTP node: **Additional Options** → **Timeout** → 60s |

---

## Sample Output

**Slack:**
```
📊 Weekly Summary: claude-builders-bounty/claude-builders-bounty

This week saw continued progress with 15 commits, 8 closed issues, and 5 merged pull requests. 
The team focused on API integration improvements and performance optimization. Notable contributions 
include enhanced error handling in the core modules and expanded test coverage...

📈 Stats: 15 commits • 8 issues closed • 5 PRs merged
```

**Discord:**
```
📊 Weekly Summary
claude-builders-bounty/claude-builders-bounty

This week brought significant activity to the repository with strong community engagement. 
Key achievements include stabilized API endpoints, improved documentation, and bug fixes 
in the authentication flow...

Commits: 15  |  Issues Closed: 8  |  PRs Merged: 5
Week of 2026-07-01
```

**Email:**
```html
<h2>Weekly Summary for claude-builders-bounty/claude-builders-bounty</h2>

<p>This week saw excellent progress across the repository...</p>

<hr>
<p><strong>Stats:</strong> 15 commits • 8 issues closed • 5 PRs merged</p>
```

---

## What Gets Included in the Summary?

✅ Commits from the past 7 days (up to 100)
✅ Closed issues from the past 7 days (up to 50)
✅ Merged PRs from the past 7 days (up to 50)
✅ Author names and commit messages
✅ Issue labels
✅ PR author information
❌ Open issues / open PRs (only closed/merged)
❌ Comments (only metadata)

---

## Advanced: Host on Docker

```yaml
version: '3'
services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      DB_TYPE: sqlite
      N8N_BASIC_AUTH_ACTIVE: "true"
      N8N_BASIC_AUTH_USER: admin
      N8N_BASIC_AUTH_PASSWORD: ${N8N_PASSWORD}
      GITHUB_API_TOKEN: ${GITHUB_API_TOKEN}
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
      SLACK_WEBHOOK: ${SLACK_WEBHOOK}
    volumes:
      - n8n_data:/home/node/.n8n
      - .env:/app/.env

volumes:
  n8n_data:
```

Run: `docker-compose up -d`

---

## Support & Resources

- **n8n Documentation:** https://docs.n8n.io
- **Claude API Docs:** https://docs.anthropic.com
- **GitHub API Docs:** https://docs.github.com/en/rest
- **n8n Community:** https://community.n8n.io

---

**Next:** Test the workflow with `/manual-test`, then activate it!
