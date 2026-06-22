# 📊 Weekly Dev Summary — n8n + Claude API

An **n8n workflow** that automatically generates a narrative weekly summary of your GitHub repo's activity, using the **Claude API**.

## Setup (5 steps)

### 1. Import the workflow
- In n8n, go to **Workflows → Add Workflow → Import from File**
- Select `weekly-dev-summary.json`

### 2. Configure credentials
| Credential | Where to get it |
|---|---|
| **GitHub** | [GitHub Settings → Tokens](https://github.com/settings/tokens) — needs `repo` scope |
| **Claude API** | [Anthropic Console](https://console.anthropic.com) — API key with claude-sonnet-4 access |
| **Slack** (optional) | [Slack Apps](https://api.slack.com/apps) — create a bot token with `chat:write` |

### 3. Configure variables
Open the **Configuration** node and set:

| Variable | Default | Description |
|---|---|---|
| `owner` | `claude-builders-bounty` | GitHub repo owner |
| `repo` | `claude-builders-bounty` | GitHub repo name |
| `language` | `EN` | Output language (`EN` or `ZH`) |
| `deliveryMethod` | `discord` | `discord` or `slack` |
| `discordWebhook` | — | Discord webhook URL |
| `slackChannel` | `#dev-updates` | Slack channel name |

### 4. Activate the workflow
Click **Active** toggle. It runs automatically every Friday at 5pm.

### 5. Test it
Click **Execute Workflow** to run a manual test. Check your Discord/Slack for the summary.

## What it generates

```
## 📊 Week in Review (Jun 15 - Jun 21)

### 🚀 Key Changes
- Added user authentication flow (3 commits)
- Implemented dark mode toggle (merged PR #42)

### 🐛 Bug Fixes
- Fixed login redirect loop (#38)
- Resolved mobile layout issue (#41)

### 👥 Contributors
@alice, @bob, @charlie

### 🔮 Looking Ahead
- API rate limiting (in progress)
- Database migration v2 (planned)
```

## Trigger

The workflow runs automatically every **Friday at 5:00 PM** via cron.

To change the schedule, edit the **Weekly Cron Trigger** node.

## Delivery Options

| Method | How to set up |
|---|---|
| **Discord** | Create a webhook in your Discord channel → paste URL into config |
| **Slack** | Create a Slack app → grant `chat:write` → set channel name |

## Sample Output

```
Weekly Development Summary
claude-builders-bounty/claude-builders-bounty
June 15 - June 21, 2026

This week saw active development with 12 commits, 5 issues closed,
and 3 merged PRs. The team focused on auth improvements and UI polish.

Key Changes:
- User authentication flow was reworked to support OAuth providers
- Dark mode toggle was added across all dashboard views
- API response caching was implemented for the search endpoint

Bug Fixes:
- Fixed #38: Login redirect loop on session expiry
- Fixed #41: Mobile navigation menu overflows on small screens

Contributors: @fanjuxin9630, @claudebounty
```

---

_Claude Builders Bounty #5 · $200_
