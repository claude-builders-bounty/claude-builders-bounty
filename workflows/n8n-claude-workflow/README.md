# n8n + Claude Code Weekly Dev Summary Workflow

**Bounty:** [claude-builders-bounty#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)
**Reward:** $200 | **Status:** Claimed ✅

## Overview

This n8n workflow automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API. Triggered every Friday at 5pm, it fetches commits, closed issues, and merged PRs, then uses Claude to write a human-readable summary delivered via Discord webhook.

## Features

- ⏰ **Weekly Cron Trigger** (Friday 5:00 PM)
- 📊 **GitHub API Integration**: commits, closed issues, merged PRs
- 🤖 **Claude API**: Generates narrative summary (claude-sonnet-4-20250514)
- 📢 **Discord Webhook Delivery**
- 🌐 **Multi-language**: EN/FR configurable
- ⚙️ **Fully Configurable**: repo, channel, language via n8n variables

## Setup (5 Steps)

### 1. Import Workflow
- Open n8n → Settings → Import → Upload `github-weekly-summary.json`

### 2. Configure Credentials
**GitHub:**
- Create Personal Access Token: GitHub Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
- Scopes needed: `contents:read`, `issues:read`, `pull_requests:read`

**Claude API:**
- Get API key: console.anthropic.com
- Create new Credential in n8n: `CLAIUDE_API_KEY`

**Discord Webhook:**
- Discord Channel → Edit Channel → Integrations → Webhooks → Create Webhook

### 3. Set Variables
In the n8n Variables section:
```
GITHUB_REPO = owner/repo-name
DISCORD_WEBHOOK_URL = https://discord.com/api/webhooks/xxx/xxx
LANGUAGE = EN
```

### 4. Activate
Toggle workflow to "Active"

### 5. Test
Click "Test Workflow" to trigger manually

## Example Output

```
📊 Weekly Dev Summary — claude-builders-bounty
📅 Week of Apr 4–10, 2026

🤖 AI Activity This Week:
• 3 new issues opened (2 enhancement, 1 bug)
• 5 pull requests merged
• 12 commits across 3 contributors

🔥 Top Contributors:
• @ai-agent (7 commits)
• @devops-bot (3 commits)
• @contributor (2 commits)

📌 Notable Changes:
• Merged Claude Code integration workflow (#42)
• Fixed Discord webhook payload issue (#41)
• Added French language support (#38)

🔮 Next Week:
• Continue bounty payouts
• Review pending PRs
```

## Workflow Structure

```
[Cron Trigger: Friday 5pm]
        ↓
[GitHub: Get Commits (last 7 days)]
        ↓
[GitHub: Get Closed Issues (last 7 days)]
        ↓
[GitHub: Get Merged PRs (last 7 days)]
        ↓
[Claude API: Generate Summary]
        ↓
[Discord: Send Message]
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Target GitHub repo (owner/name) | `claude-builders-bounty/claude-builders-bounty` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Summary language | `EN` or `FR` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-...` |
