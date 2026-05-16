# Weekly Dev Summary — n8n + Claude API

Automatically generates a weekly narrative summary of your GitHub repo activity using n8n and Claude API. Delivered every Friday at 5pm.

## What It Does

1. **Cron trigger** — runs every Friday at 5pm (configurable)
2. **Fetches from GitHub API** — commits, closed issues, merged PRs from the past 7 days
3. **Calls Claude API** (`claude-sonnet-4-20250514`) to generate a structured narrative summary
4. **Delivers via email** (SMTP) — Slack/Discord webhook alternative included in workflow notes

## Setup (5 Steps)

### 1. Import the workflow into n8n

```
n8n → Workflows → Import from File → select weekly-dev-summary.json
```

### 2. Configure n8n Variables

Go to **Variables** (top-right → Variables) and add:

| Variable | Example | Description |
|----------|---------|-------------|
| `Repo` | `claude-builders-bounty/claude-builders-bounty` | GitHub org/repo |
| `GitHub Token` | `ghp_xxx...` | GitHub personal access token (repo scope) |
| `Anthropic API Key` | `sk-ant-xxx...` | Anthropic API key |
| `SMTP From` | `bot@example.com` | Sender email |
| `SMTP To` | `team@example.com` | Recipient email |
| `Language` | `EN` or `FR` | Summary language |

### 3. Configure SMTP credentials

```
n8n → Credentials → Add Credential → SMTP
```

Fill in your SMTP host, port, user, password.

### 4. (Optional) Adjust cron schedule

Default: Friday 5pm (`0 17 * * 5`). Edit in the "Every Friday 5PM" node.

### 5. Activate the workflow

Toggle the workflow **Active** switch. Done!

## Alternative Delivery (Slack / Discord)

If you prefer Slack or Discord instead of email:

1. Open the "Send Email" node
2. Read the notes — code for Slack Webhook and Discord Webhook is included
3. Add a Slack/Discord Webhook URL variable and swap the node

## Workflow Nodes

```
Cron Trigger → Set Date Range → Fetch Commits ─┐
                               → Fetch Issues ──┼→ Build Prompt → Claude API → Format Summary → Send Email
                               → Fetch PRs ─────┘
```

## Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `Repo` | Yes | GitHub repository (owner/name) |
| `GitHub Token` | Yes | GitHub API authentication |
| `Anthropic API Key` | Yes | Claude API authentication |
| `SMTP From` | Yes | Email sender address |
| `SMTP To` | Yes | Email recipient |
| `Language` | No | Summary language: `EN` (default) or `FR` |

## Summary Format

```markdown
# Weekly Dev Summary — owner/repo

## Highlights
Key achievements this week

## What's New
Delivered features and improvements

## Fixes
Bugs squashed

## Merged PRs
| # | Title | Author |

## Contributors
Active contributors with counts

## Stats
- Commits: N
- Issues closed: N
- PRs merged: N
```

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub personal access token with `repo` scope
- Anthropic API key
- SMTP email account (or Slack/Discord webhook)
