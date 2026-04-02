# n8n + Claude Code — Weekly Development Summary

**Bounty Issue:** [#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) | **Reward:** $200

An n8n workflow that automatically generates and delivers a weekly narrative summary of a GitHub repository's activity using Claude API.

---

## Features

- ⏰ **Weekly Cron Trigger** — Runs every Friday at 5:00 PM UTC
- 📊 **Fetches GitHub Data** — Commits, closed issues, and merged PRs from the past week
- 🤖 **Claude API Integration** — Generates human-readable narrative summaries using Claude Sonnet 4
- � Discord **Webhook Delivery** — Sends summaries directly to Discord
- 🌐 **Multi-language Support** — Configurable for English (EN) or French (FR)
- ⚙️ **Fully Configurable** — All variables exposed for customization

---

## Prerequisites

1. **n8n instance** (v1.0+ recommended)
2. **GitHub Personal Access Token** — with `repo` scope for private repos, or public repo access
3. **Claude API Key** — from [Anthropic Console](https://console.anthropic.com/)
4. **Discord Webhook URL** — from your Discord server settings

---

## Setup (5 Steps)

### Step 1: Import the Workflow

1. Open your n8n instance
2. Click **"Import from File"**
3. Select `n8n-weekly-dev-summary.json`

### Step 2: Configure Variables

In n8n **Variables** panel, set the following:

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Target repository | `owner/repo-name` |
| `GITHUB_API_URL` | GitHub API base URL | `https://api.github.com` |
| `GITHUB_TOKEN` | GitHub PAT | `ghp_xxxxx` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Summary language | `EN` or `FR` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-xxxxx` |

### Step 3: Configure the Claude Node

1. Open the **Claude API - Generate Summary** node
2. Set Model to: `claude-sonnet-4-20250514`
3. Configure your API key credentials

### Step 4: Authenticate GitHub

1. Open any GitHub API node (Fetch Commits, Fetch Closed Issues, or Fetch Merged PRs)
2. Add header: `Authorization: Bearer {{ $vars.GITHUB_TOKEN }}`

### Step 5: Activate & Test

1. Toggle the workflow to **Active**
2. Click **"Test Workflow"** to run immediately
3. Verify Discord receives the summary

---

## Customizing the Prompt

The prompt sent to Claude is configured in the **Claude API** node. To customize:

**English Summary Prompt:**
```
You are a technical writer. Generate a concise, engaging weekly development summary based on the following GitHub activity:

Repository: {REPO_NAME}
Period: {WEEK_START} to {WEEK_END}

Please include:
1. Overview of the week's development activity
2. Notable commits and their impact
3. Key issues closed and their resolution
4. Merged pull requests and their significance
5. Any announcements or highlights

Write in a professional but accessible tone. Maximum 500 words.
```

**French Summary Prompt:**
```
Vous êtes un rédacteur technique. Générez un résumé hebdomadaire concis et engageant de l'activité de développement GitHub suivante:

Dépôt: {REPO_NAME}
Période: {WEEK_START} au {WEEK_END}

Veuillez inclure:
1. Aperçu de l'activité de développement de la semaine
2. Commits notables et leur impact
3. Problèmes fermés et leur résolution
4. Pull requests fusionnées et leur importance
5. Annonces ou points forts

Écrivez dans un ton professionnel mais accessible. Maximum 500 mots.
```

---

## Alternative Delivery Channels

### Slack Webhook

Replace the **Send to Discord** node with:

1. Add **Slack Node**
2. Configure Webhook URL: `{{ $vars.SLACK_WEBHOOK_URL }}`
3. Message: `{{ $json.choices[0].message.content }}`

### Email

Replace the **Send to Discord** node with:

1. Add **Email Node**
2. Configure SMTP credentials
3. Set To/From/Subject fields

---

## Screenshots

> *(To be added after successful test execution on real n8n instance)*

---

## License

MIT

---

Built with ❤️ using [n8n](https://n8n.io/) + [Claude API](https://docs.anthropic.com/)
