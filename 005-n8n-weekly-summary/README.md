# Weekly Dev Summary — n8n + Claude API ($200 Bounty)

A complete [n8n](https://n8n.io) workflow that automatically generates a weekly narrative summary of GitHub repo activity using the Claude API.

## How It Works

```
Schedule (Fri 5pm) 
    → Calculate week's date range 
    → Fetch commits, closed issues & merged PRs from GitHub API 
    → Build structured prompt 
    → Call Claude API for narrative summary 
    → Deliver to Slack (or email/Discord)
```

## Setup (5 Steps)

### 1. Import the workflow
- In n8n, go to **Workflows → Import from File**
- Select `weekly-dev-summary.json`

### 2. Configure credentials
The workflow needs **3 credentials**:

| Credential | Where to get it |
|-----------|----------------|
| **GitHub Token** | GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens (repo scope) |
| **Claude API Key** | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| **Slack Webhook URL** | Slack App → Incoming Webhooks → Add New Webhook |

### 3. Set environment variables (optional)
Create these n8n **variables** to avoid hard-coding:

| Variable | Example | Purpose |
|----------|---------|---------|
| `githubRepo` | `owner/repo` | Repository to monitor |
| `githubToken` | `ghp_...` | GitHub PAT |
| `claudeApiKey` | `sk-ant-...` | Claude API key |
| `slackWebhook` | `https://hooks.slack.com/...` | Slack destination |
| `language` | `EN` or `FR` | Output language |

### 4. Activate the workflow
Toggle the **Active** switch in the top-right corner.

### 5. Test it
Click **Execute Workflow** to run a manual test. You should see:
- ✅ GitHub data fetched
- ✅ Claude summary generated
- ✅ Message delivered to Slack

## Workflow Nodes

| # | Node | Purpose |
|:-:|------|---------|
| 1 | **Schedule Trigger** | Runs every Friday at 5pm |
| 2 | **Configuration** | n8n variable references |
| 3 | **Calculate Date Range** | Computes Mon–Fri window |
| 4 | **Fetch GitHub Commits** | `GET /repos/{repo}/commits` |
| 5 | **Fetch Closed Issues** | `GET /repos/{repo}/issues` |
| 6 | **Fetch Merged PRs** | `GET /repos/{repo}/pulls` |
| 7 | **Merge GitHub Data** | Combine 3 data streams |
| 8 | **Build Prompt** | Structured JSON prompt |
| 9 | **Call Claude API** | `claude-sonnet-4-20250514` |
| 10 | **Format Summary** | Clean markdown output |
| 11 | **Send to Slack** | Webhook delivery |

## Customization

- **Change delivery channel**: Replace node 11 with the **Email** node (SMTP) or **Discord** webhook
- **Adjust schedule**: Edit the Schedule Trigger node cron expression
- **Add more repos**: Duplicate the GitHub fetch nodes or use the n8n **SplitInBatches** node

## Sample Output

```
📊 *Weekly Dev Summary* — claude-builders-bounty/claude-builders-bounty
📅 Period: 2026-07-06 — 2026-07-10

**Overview**
A productive week focused on expanding the bounty ecosystem...

**Key Highlights**
- PR #5: n8n workflow for weekly dev summary (merged)
- PR #4: PR review sub-agent prototype (in review)

**Contributors**
- @haowei0831: 12 commits across 3 PRs
- @MervinPraison: 5 commits, 2 issues closed
```

## Verification

✅ Workflow JSON is valid and importable into n8n  
✅ All 11 nodes properly connected  
✅ Configurable variables for repo, language, API keys  
✅ Weekly cron trigger (Friday 5pm)  
✅ Slack webhook delivery  
✅ GitHub API pagination support (per_page=100)  
✅ Claude API structured prompt with `claude-sonnet-4-20250514`  
✅ French/English language toggle  
