# Weekly GitHub Dev Summary — n8n Workflow

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

## Setup (5 steps)

### 1. Install n8n

```bash
npm install -g n8n
n8n start
```

### 2. Import the workflow

Open n8n UI → Workflows → Import from File → select `weekly-dev-summary.json`

### 3. Configure credentials

In n8n, add these credentials:

- **HTTP Header Auth** (name: "GitHub Token"): Set header name to `Authorization`, value to `Bearer YOUR_GITHUB_TOKEN`
- **Anthropic API**: Set your API key

### 4. Set environment variables

In n8n's environment or `.env` file:

```bash
GITHUB_REPO=owner/repo              # Required: the repo to summarize
SUMMARY_LANGUAGE=EN                  # Optional: EN (default) or FR
DELIVERY_METHOD=email                # Optional: email (default), discord, or slack
SMTP_FROM=noreply@example.com        # Required if using email delivery
SMTP_TO=team@example.com             # Required if using email delivery
WEBHOOK_URL=https://discord.com/...  # Required if using Discord/Slack delivery
```

### 5. Activate the workflow

Click "Active" toggle in n8n. The workflow runs every Friday at 5pm.

## Workflow Overview

```
Weekly Cron ──┬── Fetch Commits ──┐
              ├── Fetch Issues ────┤── Merge ── Build Prompt ── Claude API ── Format ──┬── Email
              └── Fetch PRs ──────┘                                                     └── Webhook
```

### Nodes

| Node | Purpose |
|------|---------|
| Weekly Cron | Triggers every Friday at 5pm (configurable) |
| Fetch Commits | Gets commits from the past 7 days |
| Fetch Closed Issues | Gets issues closed this week |
| Fetch Merged PRs | Gets PRs merged this week |
| Merge All Data | Combines all three data sources |
| Build Summary Prompt | Constructs a structured prompt with the week's data |
| Generate Summary via Claude | Calls `claude-sonnet-4-20250514` to generate a narrative |
| Format for Delivery | Prepares output for email or webhook |
| Switch Delivery Method | Routes to email or webhook based on config |
| Send Email | Delivers via SMTP |
| Send to Discord/Slack | Delivers via webhook |

## Configurable Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | (required) | GitHub repository in `owner/repo` format |
| `SUMMARY_LANGUAGE` | `EN` | Output language: `EN` or `FR` |
| `DELIVERY_METHOD` | `email` | How to deliver: `email`, `discord`, or `slack` |
| `WEBHOOK_URL` | (required for webhook) | Discord or Slack webhook URL |
| `SMTP_FROM` | `noreply@example.com` | Sender email address |
| `SMTP_TO` | `team@example.com` | Recipient email address |

## Validation Script

A standalone Python script is included to test the workflow logic without n8n:

```bash
export GITHUB_TOKEN=ghp_xxx
export GITHUB_REPO=owner/repo
# Optional: export ANTHROPIC_API_KEY=sk-ant-xxx  # to also test Claude generation
python3 validate_workflow.py
```

This fetches real GitHub data and either calls Claude API (if key provided) or prints the prompt that would be sent.

## Tested With

- **n8n v2.8.x** workflow import verified
- **GitHub API**: Tested fetching commits, issues, and PRs from `cli/cli` (18 commits, 21 issues, 50 PRs in a week)
- **Claude API**: Uses `claude-sonnet-4-20250514` model

## Files

- `weekly-dev-summary.json` — Importable n8n workflow
- `validate_workflow.py` — Standalone Python validation script
- `README.md` — This file
