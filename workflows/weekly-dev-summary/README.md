# 🏆 Bounty #5 — n8n Weekly Dev Summary Workflow

**Prize: $200** · **Status:** 🟢 Open for submission

Automatically generate a weekly development summary for any GitHub repository using n8n + Claude AI. Every Friday at 5 PM, the workflow fetches the week's commits, closed issues, and merged PRs, sends them to Claude for a narrative summary, and delivers the result via email **and/or** Discord/Slack webhook.

---

## 🧠 How It Works

```
┌─────────────────┐     ┌───────────────────┐     ┌──────────────────────┐
│  Schedule       │────▶│  Set Config       │────▶│  Code: Fetch GitHub  │
│  Cron (Fri 5pm) │     │  Variables         │     │  Data                │
└─────────────────┘     └───────────────────┘     └──────────┬───────────┘
                                                             │
                                                             ▼
┌─────────────────┐     ┌───────────────────┐     ┌──────────────────────┐
│  Code: Format   │◀────│  HTTP Request:    │◀────│  Code: Build Claude  │
│  Response       │     │  Call Claude API  │     │  Prompt              │
└────────┬────────┘     └───────────────────┘     └──────────────────────┘
         │
         ┌──────────────────────┐
         │                      ▼
         │           ┌──────────────────────┐
         │           │  Email: Send Summary  │
         │           └──────────────────────┘
         │
         ▼
┌──────────────────────┐
│  Webhook: Discord/   │
│  Slack               │
└──────────────────────┘
```

### Node Overview

| # | Node | Type | Purpose |
|---|------|------|---------|
| 1 | **Weekly Schedule (Fri 5pm)** | `scheduleTrigger` | Cron: `0 17 * * 5` — fires every Friday at 5 PM |
| 2 | **Set Config Variables** | `set` | Configure repo owner, repo name, language, delivery targets |
| 3 | **Fetch GitHub Data** | `code` | Makes 3 GitHub API calls (commits, issues, PRs), handles pagination |
| 4 | **Build Claude Prompt** | `code` | Formats the fetched data into a structured prompt (supports EN/AR) |
| 5 | **Call Claude API** | `httpRequest` | POST to `api.anthropic.com/v1/messages` with `claude-sonnet-4-20250514` |
| 6 | **Format Claude Response** | `code` | Extracts text from Claude's structured response |
| 7 | **Send Email Summary** | `emailSend` | Delivers via SMTP email |
| 8 | **Send Webhook** | `httpRequest` | Delivers to Discord or Slack webhook URL |

---

## ⚙️ Setup (5 Steps)

### Step 1: Prerequisites

- **n8n** instance (self-hosted, n8n.cloud, or Docker) — v1.0+
- **GitHub Personal Access Token** with `repo` scope ([create one](https://github.com/settings/tokens))
- **Anthropic API Key** for Claude ([get one](https://console.anthropic.com/))
- **SMTP credentials** (for email delivery) **or** a Discord/Slack webhook URL

### Step 2: Import the Workflow

1. In n8n, go to **Workflows** → **Add Workflow** → **Import from File**
2. Select `weekly-dev-summary-workflow.json`
3. The workflow appears with 8 pre-configured nodes

### Step 3: Configure Credentials

#### a) GitHub Personal Access Token

Create a credential of type **"GitHub Personal Access Token"** named **"GitHub PAT"**:

| Field | Value |
|-------|-------|
| **Credential Type** | GitHub Personal Access Token |
| **Name** | `GitHub PAT` |
| **Access Token** | `ghp_xxxxxxxxxxxxxxxxxxxx` (your token) |

> **Alternative:** Set the `GITHUB_TOKEN` environment variable in your n8n deployment. The Code node will fall back to `process.env.GITHUB_TOKEN` automatically.

#### b) Claude / Anthropic API Key

Create a credential of type **"Header Auth"** named **"Anthropic API"**:

| Field | Value |
|-------|-------|
| **Credential Type** | Header Auth |
| **Name** | `Anthropic API` |
| **Header Name** | `x-api-key` |
| **Header Value** | `sk-ant-xxxxxxxxxxxxxxxxxxxx` (your API key) |

Then, on the **"Call Claude API"** node:

1. Open the node
2. Under **Authentication** → **Credential for Header Auth**, select **"Anthropic API"**

#### c) SMTP (Email Delivery)

Create a credential of type **"SMTP"** named **"SMTP"**:

| Field | Value |
|-------|-------|
| **Credential Type** | SMTP |
| **Name** | `SMTP` |
| **User** | Your SMTP username (usually the email address) |
| **Password** | Your SMTP password or app password |
| **Host** | e.g., `smtp.gmail.com` |
| **Port** | `465` (SSL) or `587` (TLS) |
| **SSL/TLS** | Enabled for port 465 |

Then, on the **"Send Email Summary"** node:

1. Open the node
2. Under **Credential for SMTP**, select **"SMTP"**
3. Update the **From Email** address to match your SMTP user

### Step 4: Configure Variables

Open the **"Set Config Variables"** node and adjust:

| Variable | Default | Description |
|----------|---------|-------------|
| `repoOwner` | `claude-builders-bounty` | GitHub owner (user or org) |
| `repoName` | `claude-builders-bounty` | GitHub repository name |
| `deliveryEmail` | `team@example.com` | Where to send the email summary |
| `deliveryWebhook` | *(empty)* | Discord/Slack webhook URL (leave empty to skip) |
| `language` | `en` | Output language: `en` (English) or `ar` (Arabic) |

### Step 5: Activate

1. Click **Save** on the workflow
2. Toggle **Active** to enable the cron schedule
3. To test immediately, click **Execute Workflow** (manual run)

---

## 🌐 Delivery Options

### Email

The **Send Email Summary** node sends the Claude-generated summary to the address in `deliveryEmail`. The subject line includes the repo name and date range.

### Discord / Slack Webhook

To use webhook delivery instead of (or in addition to) email:

1. Create a webhook in your Discord channel or Slack workspace
2. Set the webhook URL as the `deliveryWebhook` value in the **Set Config Variables** node
3. Leave `deliveryWebhook` empty to skip webhook delivery

> **Note:** Discord webhooks expect `{"content": "..."}`. Slack webhooks expect `{"text": "..."}`. To switch formats, edit the **"Send Webhook"** node's body parameter name from `content` to `text`.

---

## 🧪 Testing & Verification

### Manual Test Run

1. Open the workflow in n8n
2. Click **Execute Workflow** (the play button)
3. n8n runs every node in sequence and shows the output of each

### What to Verify

| Check | Expected Result |
|-------|-----------------|
| **Schedule Trigger** | Fires immediately (manual runs bypass cron) |
| **Set Config Variables** | Outputs your configured values |
| **Fetch GitHub Data** | `commits`, `issues`, `pullRequests` arrays with data (or empty arrays) |
| **Build Claude Prompt** | Produces `systemPrompt` + `userPrompt` strings |
| **Call Claude API** | HTTP 200 with a `content` array containing the summary text |
| **Format Claude Response** | `summary` string extracted from Claude's response |
| **Send Email** | Email sent (check inbox, including spam) |
| **Send Webhook** | HTTP 204 (Discord) or HTTP 200 (Slack) |

### Verifying GitHub Data

After running, inspect the **Fetch GitHub Data** node's output:

- **Commits**: Should list commits from Mon–Fri of the current week
- **Issues**: Issues that were closed during the week (excluding PRs)
- **PRs**: Pull requests that were merged during the week

If any array is empty, the workflow still works — Claude will report "no activity this week" gracefully.

### Cron Schedule

The default schedule is `0 17 * * 5` (Friday at 5 PM in the workflow's timezone). To change it:

1. Open the **Weekly Schedule (Fri 5pm)** node
2. Edit the **Cron Expression** field
3. Common alternatives:
   - `0 9 * * 1` — Monday 9 AM (for a previous-week report)
   - `0 12 * * 6` — Saturday 12 PM (end-of-week report)

The workflow timezone is set in **Workflow Settings** → **Timezone** (default: `America/New_York`).

### Rate Limiting

GitHub API has a limit of 5,000 requests/hour for authenticated users. This workflow makes at most 3–6 requests per execution, so rate limiting is not a concern for weekly runs.

---

## 🔧 Customization

### Adding More Repositories

To monitor multiple repos, either:
1. **Duplicate** the workflow and change `repoOwner`/`repoName`
2. **Use n8n tools**: Add an `n8n-nodes-base.splitInBatches` node and iterate over a list of repos

### Changing the Claude Model

Edit the `model` field in the **Call Claude API** node's body parameters. Default is `claude-sonnet-4-20250514`.

### Changing Summary Style

Modify the `systemPrompt` in the **Build Claude Prompt** Code node. For example:

```javascript
const systemPrompt = 'Write the summary as bullet points only, no prose.';
```

### Adding Slack Block Formatting

To format the summary as a Slack Block Kit message, change the **"Send Webhook"** node's body to:

```json
{
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "={{ $json.summary }}"
      }
    }
  ]
}
```

---

## 🛠 Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `GitHub credential not found` | Missing GitHub PAT credential | Create "GitHub PAT" credential or set `GITHUB_TOKEN` env var |
| HTTP 401 from Anthropic API | Missing or invalid `x-api-key` header | Check the "Anthropic API" Header Auth credential |
| HTTP 403 from GitHub API | Rate limited or insufficient scope | Verify token has `repo` scope; wait 1 hour if rate limited |
| Email not delivered | Wrong SMTP settings or spam filter | Check SMTP credential; check spam folder; use app-specific password |
| Webhook returns 400 | Wrong format for Discord/Slack | Switch body key from `content` (Discord) to `text` (Slack) |
| `$credentials is not defined` | Old n8n version | Upgrade to n8n v1.0+; the Code node requires modern `$credentials` support |
| Empty "issues" array | No issues closed this week, OR API returns PRs | PRs are filtered correctly by the Code node; empty is normal |

---

## 📁 File Structure

```
workflows/weekly-dev-summary/
├── weekly-dev-summary-workflow.json    # n8n importable workflow (all 8 nodes)
└── README.md                           # This file
```

---

## 📜 License

Part of [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty). See the repository LICENSE.
