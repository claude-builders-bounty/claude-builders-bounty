# GitHub Weekly Dev Summary — n8n Workflow

Generate a **weekly narrative summary** of GitHub repo activity using **n8n + Claude API**. Delivered every Friday at 5pm to Discord, Slack, or Email.

## Setup (5 Steps)

### 1. Import the Workflow
- Open n8n (usually `http://localhost:5678`)
- Go to **Workflows** → **Import from File**
- Select `github-weekly-summary.json`

### 2. Configure Credentials

| Credential | Type | Where to Get It |
|---|---|---|
| **GitHub** | Header Auth (Bearer token) | [GitHub Token](https://github.com/settings/tokens) — needs `repo` scope |
| **Claude API** | Header Auth (x-api-key) | [Anthropic Console](https://console.anthropic.com) — use key with `claude-sonnet-4-20250514` access |

In n8n, go to **Credentials** → **Add Credential**:
- `github` → `Header Auth` (enter token as `Bearer <token>` value)
- `claudeApi` → `Header Auth` (enter your Anthropic API key)

### 3. Configure Variables
Open the **Config** node in the workflow and edit:
- `githubRepo` — e.g. `vercel/next.js`
- `lang` — `EN` (English) or `FR` (French)
- `deliveryType` — `discord`, `slack`, or `email`
- `webhookUrl` — webhook URL (for Discord/Slack)
- `emailTo` — email address (for email delivery)

### 4. Activate the Workflow
- Click **Save** (Ctrl+S)
- Toggle the **Active** switch to enable the weekly cron schedule
- Default: **Friday 5pm UTC**

### 5. Test It
- Click **Execute Workflow** to run a manual test
- If successful, you'll receive a summary like the one below

---

## What It Does

| Step | Node | Description |
|---|---|---|
| ⏰ | **Schedule Trigger** | Cron: `0 17 * * 5` (Fri 5pm UTC) |
| ⚙️ | **Config** | Configurable variables (repo, language, delivery) |
| 📦 | **Fetch Commits** | `GET /repos/{repo}/commits` — last 7 days |
| 📋 | **Fetch Issues** | `GET /repos/{repo}/issues` — closed this week |
| 🔀 | **Fetch PRs** | `GET /repos/{repo}/pulls` — merged this week |
| 🧩 | **Merge Data** | Combines 3 API results, filters & formats |
| 🤖 | **Claude Summary** | Calls `claude-sonnet-4-20250514` with data |
| 📝 | **Extract Response** | Extracts text from Claude's response |
| 🔀 | **Route Delivery** | Switch: Discord / Slack / Email |
| 📤 | **Send** | Posts the formatted summary |

All 3 GitHub fetches run **in parallel** for speed.

## Output Example

```
📊 Weekly Dev Summary — vercel/next.js
Week ending: 2026-05-19

### Overview
A productive week with 47 commits, 12 merged PRs, and 8 closed issues...

### 🚀 Merged PRs
- #72143: Optimize static generation cache (#72143) by @user
- #72118: Fix turbopack HMR race condition by @user

### 🐛 Issues Resolved
- #72100: Server Actions not revalidating in production
- #72085: Metadata API regression in 15.2.1

### 📊 Stats
- Commits: 47 | PRs Merged: 12 | Issues Closed: 8
```

## Requirements

- n8n v1.x+ (self-hosted or n8n.cloud)
- GitHub token with `repo` scope
- Anthropic API key
- Discord/Slack webhook URL OR SMTP email credentials
