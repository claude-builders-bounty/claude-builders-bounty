# 📊 n8n + Claude Code — Automated Weekly Dev Summary

**Bounty:** [#5 — WORKFLOW: n8n + Claude Code — automated weekly dev summary](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)
**Reward:** $200
**Status:** ✅ Submitted

## Overview

An n8n workflow that runs every Monday, fetches your GitHub activity (commits, PRs, issues) from the past week, uses Claude Sonnet 4 to generate a professional summary, and delivers it via email and/or Slack.

## Quick Setup (≤ 5 steps)

### 1. Prerequisites

- [n8n](https://n8n.io/) instance (self-hosted or cloud)
- [GitHub Personal Access Token](https://github.com/settings/tokens) (repo scope)
- [Anthropic API Key](https://console.anthropic.com/) for Claude Sonnet
- Optional: SMTP credentials or Slack webhook

### 2. Import Workflow

```bash
# Download the workflow
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/submissions/5-n8n-workflow/weekly-dev-summary.json
```

1. Open n8n dashboard
2. Go to **Workflows** → **Import from File**
3. Select `weekly-dev-summary.json`

### 3. Configure Credentials

In n8n, add these credentials:

| Credential | Type | How to Get |
|-----------|------|------------|
| `github-api` | HTTP Request | GitHub PAT with `repo` scope |
| `claude-api-key` | Anthropic API | console.anthropic.com |
| `smtp-credentials` | SMTP | Your email provider |

### 4. Set Repository

Edit the **🔧 Build Context** node and change the repository URL:

```javascript
// Change this line:
const repoUrl = 'https://api.github.com/repos/your-org/your-repo';
```

### 5. Activate

Toggle the workflow to **Active**. It will run every Monday at 9 AM.

## Output Format

```
📊 Weekly Dev Summary — my-org/my-repo (Jul 3 - Jul 10)

⭐ Highlights
- Shipped user dashboard v2 with real-time analytics
- Fixed critical auth bypass vulnerability (CVE-2026-1234)
- Reduced API latency by 40% through query optimization

📈 Progress
- 28 commits (+15% vs last week)
- 6 PRs merged (3 features, 2 fixes, 1 chore)
- 4 new issues opened, 3 closed

🐛 Bug Fixes
- Fixed session timeout handling in auth middleware
- Resolved memory leak in WebSocket connections
- Patched XSS vulnerability in markdown renderer

🎯 Focus for Next Week
- Complete Stripe integration for payment processing
- Begin database migration to Turso
- Update API documentation for v2 endpoints
```

## Delivery Methods

| Method | Configured | Description |
|--------|-----------|-------------|
| 📧 Email | ✅ | SMTP delivery to team/individual |
| 💬 Slack | ✅ | Webhook to channel or DM |
| 🔗 Webhook | 🟡 Optional | Custom endpoint for further processing |

## Testing

- ✅ Workflow imports cleanly into n8n
- ✅ GitHub API fetches commits, PRs, and issues
- ✅ Claude Sonnet generates structured summary
- ✅ Email and Slack delivery work end-to-end

## Files

- `weekly-dev-summary.json` — n8n workflow export
- `README.md` — This file
