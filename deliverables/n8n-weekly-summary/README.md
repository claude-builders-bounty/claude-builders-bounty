# Weekly GitHub Dev Summary — n8n Workflow

> Automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

---

## 🚀 Setup (5 Steps)

### Step 1: Import the Workflow

1. Open your n8n instance (cloud or self-hosted)
2. Go to **Workflows** → **Import from File**
3. Select `workflow.json`

### Step 2: Configure Credentials

In the imported workflow, set up these credentials:

| Credential | Type | Where to Get |
|------------|------|-------------|
| **GitHub API** | OAuth2 / Personal Access Token | [github.com/settings/tokens](https://github.com/settings/tokens) — needs `repo` scope |
| **Anthropic API** | HTTP Header Auth | [console.anthropic.com](https://console.anthropic.com) — API Key for `claude-3-5-sonnet-20241022` |

Double-click each HTTP Request node and paste the credentials.

### Step 3: Configure Variables

Edit the **Weekly Cron** node or add an **Edit Fields** node at the start with these values:

| Variable | Description | Example |
|----------|-------------|---------|
| `repo` | GitHub repo to monitor | `owner/repo` |
| `language` | Summary language | `en` or `fr` |
| `discordWebhook` | Discord webhook URL (optional) | `https://discord.com/api/webhooks/...` |
| `slackWebhook` | Slack webhook URL (optional) | `https://hooks.slack.com/services/...` |

> **Note:** At least one webhook (Discord or Slack) must be configured for delivery.

### Step 4: Activate the Workflow

1. Click **Activate** in the top-right corner
2. The workflow runs every **Friday at 5:00 PM** (server timezone)
3. To change the schedule, edit the **Weekly Cron** node's cron expression

### Step 5: Test Manually

Click **Execute Workflow** to run it immediately and verify the output.

---

## 📋 How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Weekly Cron │────▶│ Calculate Week   │────▶│ Fetch from   │
│ (Fri 5 PM)  │     │ Dates            │     │ GitHub API   │
└─────────────┘     └──────────────────┘     └──────┬───────┘
                                                     │
                    ┌────────────────────────────────┼────────────────────────────────┐
                    ▼                                ▼                                ▼
             ┌─────────────┐                ┌──────────────┐                ┌──────────────┐
             │   Commits   │                │ Closed Issues│                │  Merged PRs  │
             └──────┬──────┘                └──────┬───────┘                └──────┬───────┘
                    │                                │                                │
                    └────────────────────────────────┼────────────────────────────────┘
                                                     ▼
                                            ┌──────────────┐
                                            │  Aggregate   │
                                            │    Data      │
                                            └──────┬───────┘
                                                   ▼
                                            ┌──────────────┐
                                            │   Claude API │
                                            │  (Sonnet 4)  │
                                            └──────┬───────┘
                                                   ▼
                                            ┌──────────────┐
                                            │ Format Output│
                                            └──────┬───────┘
                    ┌──────────────────────────────┼──────────────────────────────┐
                    ▼                              ▼                              ▼
           ┌─────────────┐               ┌──────────────┐               ┌──────────────┐
           │   Discord   │               │    Slack     │               │    Console   │
           │   Webhook   │               │   Webhook    │               │     Log      │
           └─────────────┘               └──────────────┘               └──────────────┘
```

## 📊 What Gets Fetched

| Data | API Endpoint | Filter |
|------|-------------|--------|
| **Commits** | `/repos/{owner}/{repo}/commits` | `since` / `until` = week range |
| **Closed Issues** | `/repos/{owner}/{repo}/issues` | `state=closed`, `since` / `until` |
| **Merged PRs** | `/repos/{owner}/{repo}/pulls` | `state=closed`, `merged_at` present |

## 🤖 Claude Prompt

The workflow sends the aggregated data to **Claude 3.5 Sonnet** with this prompt structure:

```
Write a weekly development summary for {repo}
Period: {weekStart} to {weekEnd}

Statistics:
- Total commits: {count}
- Merged pull requests: {count}
- Closed issues: {count}

Top Contributors: {list}
Merged Pull Requests: {list}
Closed Issues: {list}

Language: {en/fr}
```

## 📤 Delivery Options

| Channel | Format | Setup |
|---------|--------|-------|
| **Discord** | Rich embed with fields | Webhook URL |
| **Slack** | Block Kit with markdown | Incoming Webhook |
| **Console** | Plain text log | Built-in (no config) |

## ⚙️ Customization

### Change the Schedule

Edit the **Weekly Cron** node:

| Expression | Meaning |
|------------|---------|
| `0 17 * * 5` | Every Friday at 5 PM (default) |
| `0 9 * * 1` | Every Monday at 9 AM |
| `0 12 * * *` | Daily at noon |

### Change the Model

Edit the **Generate Summary (Claude)** node:

```json
"model": "claude-3-5-sonnet-20241022"  // → "claude-3-opus-20240229" or others
```

### Add Email Delivery

Add an **Email Send** node connected to **Format Output**:

```
Format Output → Email Send (SMTP)
```

Configure SMTP credentials in n8n and set recipient.

### Add More GitHub Data

Add additional HTTP Request nodes for:

- `/repos/{repo}/releases` — Recent releases
- `/repos/{repo}/actions/runs` — CI/CD status
- `/repos/{repo}/contributors` — Top contributors

---

## 🔒 Security Notes

- GitHub token needs only `repo` (read) scope
- Claude API key is stored in n8n credentials (encrypted at rest)
- Webhook URLs are stored in n8n credentials
- No data is stored externally — all processing happens in your n8n instance

---

## 📦 Files

| File | Description |
|------|-------------|
| `workflow.json` | Importable n8n workflow |
| `README.md` | This file |

---

## Bounty

**$200** — [claude-builders-bounty/claude-builders-bounty#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)
