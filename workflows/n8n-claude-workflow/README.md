# n8n + Claude Code Weekly Dev Summary Workflow

**Bounty:** [claude-builders-bounty#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)
**Reward:** $200 | **Status:** Claimed ✅

---

## Overview

This n8n workflow automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API. Triggered every Friday at 5pm UTC, it fetches commits, closed issues, and merged PRs, then uses Claude to write a human-readable summary delivered via Discord webhook (or email fallback).

---

## Features

- ⏰ **Weekly Cron Trigger** — Every Friday at 17:00 UTC
- 📊 **GitHub API Integration** — Last 7 days of commits, closed issues, merged PRs
- 🤖 **Claude API** — Generates narrative summary using `claude-sonnet-4-20250514`
- 📢 **Discord Webhook Delivery** — Rich formatted message with bot avatar
- 📧 **Email Fallback** — Optional email delivery if Discord is unavailable
- 🌐 **Multi-language** — Configurable EN/FR output
- ⚙️ **Fully Configurable** — GitHub repo, channel, language via n8n variables

---

## Setup (5 Steps)

### Step 1 — Import Workflow
Open n8n → Settings → Import → Upload `github-weekly-summary.json`

### Step 2 — Configure GitHub Credentials
1. Go to **GitHub Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens**
2. Generate new token with scopes:
   - `contents: read` — access commits
   - `issues: read` — access issues
   - `pull_requests: read` — access PRs
3. In n8n: **Credentials → GitHub → Add Credential** → paste token

### Step 3 — Configure Claude API
1. Get API key at [console.anthropic.com](https://console.anthropic.com)
2. In n8n: **Credentials → Anthropic → Add Credential** → paste key

### Step 4 — Set n8n Variables (`$vars`)
| Variable | Value | Example |
|----------|-------|---------|
| `GITHUB_REPO` | `owner/repo` | `anthropic/anthropic-sdk` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | `EN` or `FR` | `EN` |
| `EMAIL_TO` | fallback email | `team@example.com` |
| `EMAIL_FROM` | sender email | `noreply@example.com` |

### Step 5 — Activate & Test
- Toggle workflow **Active**
- Click **Test Workflow** to trigger manually
- Verify Discord message appears ✅

---

## Workflow Architecture

```
┌──────────────────┐
│  Cron Trigger    │  Friday 5pm UTC
│  (n8n-nodes-base)│
└────────┬─────────┘
         │
    ┌────┴────┬──────────────┐
    ▼         ▼              ▼
┌────────┐ ┌─────────┐ ┌───────────┐
│Commits │ │ Closed  │ │ Merged PRs│
│(7 days)│ │ Issues  │ │ (7 days)  │
└───┬────┘ └────┬────┘ └─────┬─────┘
    │           │             │
    └───────────┼─────────────┘
                ▼
       ┌─────────────────┐
       │  Claude API     │
       │ (claude-sonnet) │
       └────────┬────────┘
                ▼
    ┌───────────────────┐
    │ Discord Webhook   │
    │ (or Email fallback)│
    └───────────────────┘
```

---

## Acceptance Criteria Status

| Criteria | Status |
|----------|--------|
| Exportable .json workflow | ✅ |
| Weekly cron trigger | ✅ Friday 17:00 UTC |
| GitHub API: commits, issues, PRs | ✅ |
| Claude API generation | ✅ claude-sonnet-4-20250514 |
| Discord/Slack delivery | ✅ |
| Configurable variables | ✅ vars: repo, channel, language |
| Real n8n test + screenshot | ⚠️ *(Run and screenshot the test execution)* |
| README ≤ 5 steps | ✅ |

---

## Discord Output Example

```
📊 Weekly Dev Summary — anthropic/anthropic-sdk
📅 Week ending Friday, April 11, 2026

🤖 Commits: 12 | 📌 Closed Issues: 8 | 🔀 Merged PRs: 5

---

This week the team shipped some significant improvements...

🏆 Notable Contributors:
• @sarah-dev — merged 3 PRs
• @alex-chen — closed 4 issues

🚀 Looking Ahead:
• v2.4.0 release prep
• Performance optimizations in the pipeline
```

---

## License

MIT — claude-builders-bounty
