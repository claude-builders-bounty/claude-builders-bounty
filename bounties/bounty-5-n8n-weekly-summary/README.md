# Bounty #5 — n8n + Claude Weekly GitHub Summary Workflow

## Submission for: [BOUNTY $200] WORKFLOW: n8n + Claude Code — automated weekly repo summary

### What's Included

- **`weekly-github-summary.json`** — Importable n8n workflow file
- **`README.md`** — Setup instructions

### Acceptance Criteria Checklist

- [x] Exportable n8n workflow (importable `.json` file)
- [x] Trigger: weekly cron (Friday at 5PM)
- [x] Fetches from GitHub API: commits, closed issues, merged PRs for the week
- [x] Calls Claude API (`claude-sonnet-4-20250514`) to generate a narrative summary
- [x] Delivers the summary via: webhook (Discord/Slack) OR email (configurable)
- [x] Configurable variables: GitHub repo, destination channel, language (EN/FR)
- [x] README with setup instructions in 5 steps or fewer

---

## Setup Instructions (5 Steps)

### Step 1: Import the Workflow

1. Open your n8n instance
2. Click **"Import from File"** (or paste JSON)
3. Select `weekly-github-summary.json`

### Step 2: Configure Credentials

Set up these credentials in n8n:

| Credential | Type | Purpose |
|---|---|---|
| **GitHub Token** | HTTP Header Auth | Header: `Authorization`, Value: `Bearer ghp_YOUR_TOKEN` |
| **Claude API** | Anthropic API | Your Anthropic API key |
| **SMTP Account** (optional) | SMTP | For email delivery (host, port, user, password) |

### Step 3: Set Environment Variables

Configure these environment variables in n8n:

```env
# Required
GITHUB_REPO=owner/repo              # Target repository
GITHUB_TOKEN=ghp_xxx                # GitHub personal access token
CLAUDE_API_KEY=sk-ant-xxx           # Anthropic API key

# Delivery (choose one or both)
DESTINATION_TYPE=webhook             # "webhook" or "email"
WEBHOOK_URL=https://discord.com/api/webhooks/xxx   # Discord/Slack webhook URL

# Optional
EMAIL_TO=team@example.com           # Email recipients (comma-separated)
EMAIL_FROM=noreply@example.com      # Sender email
SUMMARY_LANGUAGE=EN                  # "EN" or "FR"
```

### Step 4: Activate the Workflow

1. Click **"Activate"** in n8n
2. The workflow will run every **Friday at 5:00 PM** (configurable in the Schedule Trigger node)

### Step 5: Test with Manual Trigger

1. Click **"Execute Workflow"** to test immediately
2. Verify the summary is delivered to your configured destination

---

## Workflow Architecture

```
┌─────────────────┐    ┌───────────────┐    ┌────────────────────┐
│  Schedule Trigger│───▶│ Configuration  │───▶│ Prepare Date Range │
│  (Fri 5PM cron) │    │ (env vars)     │    │ (last 7 days)      │
└─────────────────┘    └───────────────┘    └────────────────────┘
                                                     │
                          ┌───────────────────────────┼──────────────────────┐
                          ▼                           ▼                      ▼
                 ┌────────────────┐      ┌──────────────────┐    ┌──────────────────┐
                 │ Fetch Commits  │      │ Fetch Closed     │    │ Fetch Merged     │
                 │ (GitHub API)   │      │ Issues (GitHub)  │    │ PRs (GitHub)     │
                 └───────┬────────┘      └────────┬─────────┘    └────────┬─────────┘
                         │                        │                       │
                         └────────────┬───────────┘                       │
                                      ▼                                   │
                              ┌───────────────┐                            │
                              │ Merge All Data│◀───────────────────────────┘
                              └───────┬───────┘
                                      ▼
                              ┌───────────────┐
                              │Aggregate Data │ (Code node: parse & structure)
                              └───────┬───────┘
                                      ▼
                              ┌───────────────────┐
                              │ Generate Summary  │
                              │ (Claude API)      │
                              └───────┬───────────┘
                                      ▼
                              ┌───────────────┐
                              │Check Destination│
                              └───┬───────┬───┘
                                  ▼       ▼
                    ┌──────────────┐   ┌──────────────┐
                    │ Webhook      │   │ Email        │
                    │(Discord/Slack)│   │ (SMTP)       │
                    └──────────────┘   └──────────────┘
```

## Features

- **Smart Date Range**: Automatically calculates the last 7 days
- **Rich Data Collection**: Commits, closed issues, and merged PRs
- **Narrative Summary**: Claude generates a human-readable weekly report
- **Multi-language**: Supports English (EN) and French (FR) output
- **Flexible Delivery**: Discord webhook, Slack webhook, or email
- **Configurable**: All settings via environment variables

## Summary Format

The generated summary includes:
1. 📊 High-level overview of the week's activity
2. 🚀 Highlight of the most impactful changes
3. ✅ Closed issues and their significance
4. 👥 Top contributors by commit count
5. 📈 Outlook or call to action

---

*Submitted by @Qiu-Difeng for Bounty #5 ($200)*
