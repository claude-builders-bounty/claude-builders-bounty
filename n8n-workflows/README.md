# 📊 GitHub Weekly Dev Summary — n8n Workflow

An automated **n8n workflow** that generates narrative weekly summaries of GitHub repository activity using **Claude API** (claude-sonnet-4-20250514).

## Features

- ✅ **Weekly cron trigger** — Every Friday at 5:00 PM
- ✅ **Fetches GitHub data** — Commits, closed issues, merged PRs
- ✅ **AI-powered summary** — Uses Claude Sonnet 4 to generate narrative prose
- ✅ **Discord delivery** — Posts summary to any Discord channel via webhook
- ✅ **Configurable** — GitHub repo, webhook URL, language (EN/FR)

---

## Architecture

```
Schedule (Fri 5pm)
    ↓
Set Config Variables
    ├──────────┬──────────┐
    ↓          ↓          ↓
Fetch Commits  Fetch Issues  Fetch PRs
    ├──────────┴──────────┘
    ↓
Merge GitHub Data (Code Node)
    ↓
Generate Summary with Claude (claude-sonnet-4-20250514)
    ↓
Extract Summary (Code Node)
    ↓
Post to Discord Webhook
```

---

## Setup Instructions (5 Steps)

### Step 1: Import the Workflow

1. Open your **n8n instance** (self-hosted or cloud)
2. Go to **Workflows** → **Import from File**
3. Select `n8n-workflows/github-weekly-summary.json`
4. Click **Import**

### Step 2: Configure Credentials

**GitHub Token:**
- Create a [GitHub Personal Access Token](https://github.com/settings/tokens) with `repo` scope
- In n8n, go to **Credentials** → **Add Credential** → **Header Auth**
- Name it `GitHub Header Auth` and set:
  - Header Name: `Authorization`
  - Header Value: `Bearer YOUR_GITHUB_TOKEN`

**Anthropic API Key:**
- Get your key from [console.anthropic.com](https://console.anthropic.com)
- Set as environment variable: `ANTHROPIC_API_KEY`

### Step 3: Set Environment Variables

In n8n, go to **Settings** → **Environment Variables** and add:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Target repository (owner/repo) | `claude-builders-bounty/claude-builders-bounty` |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxx...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-xxxx...` |
| `DISCORD_WEBHOOK_URL` | Discord channel webhook URL | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Output language (`en` or `fr`) | `en` |

### Step 4: Create Discord Webhook

1. Go to your Discord server → **Server Settings** → **Integrations** → **Webhooks**
2. Click **New Webhook**
3. Choose the channel for dev summaries
4. Copy the **Webhook URL**
5. Set it as the `DISCORD_WEBHOOK_URL` environment variable in n8n

### Step 5: Activate & Test

1. Open the imported workflow in n8n
2. Click **Execute Workflow** (manual test)
3. Check your Discord channel for the summary
4. Toggle the **Active** switch to enable the weekly schedule

---

## Output Format

The workflow generates a narrative summary like:

```markdown
## 📊 Weekly Dev Summary — owner/repo

This week in owner/repo, we saw 23 commits from 5 contributors! 
The team closed 8 issues and merged 4 pull requests, including 
the highly anticipated feature by @contributor that adds...

Top contributors this week were @alice (12 commits), @bob (7), 
and @charlie (4)...
```

---

## Customization

### Change Schedule

Edit the **Weekly Schedule** node:
- Go to node settings
- Change `triggerAtHour` and `triggerAtMinute`
- Change `triggerAtDay` (0=Sunday, 5=Friday, 6=Saturday)

### Switch to Slack

Replace the **Post to Discord** node with an HTTP Request to Slack:
```
POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
Body: { "text": "## Weekly Dev Summary\n\n{{ $json.summary }}" }
```

### Change Claude Model

Edit the **Generate Summary with Claude** node and change:
```json
"model": "claude-sonnet-4-20250514"
```

### Add Email Delivery

Add an **Email (SMTP)** node after **Extract Summary**:
- Connect it in parallel to the Discord node
- Configure SMTP credentials
- Set subject: `Weekly Dev Summary - {{ $json.repo }}`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No data fetched | Check `GITHUB_TOKEN` has `repo` scope |
| Claude API error | Verify `ANTHROPIC_API_KEY` is valid |
| Discord post fails | Ensure webhook URL is correct and channel exists |
| Empty summary | Check repo has recent activity in the date range |

---

## File Structure

```
n8n-workflows/
├── github-weekly-summary.json    # Importable n8n workflow
└── README.md                     # This file
```

---

## License

MIT
