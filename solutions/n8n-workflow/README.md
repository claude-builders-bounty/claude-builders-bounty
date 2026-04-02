# 🤖 Weekly Dev Summary — n8n + Claude Workflow

Automated weekly development summary that fetches GitHub activity and uses Claude AI to generate a narrative report delivered to Discord (or Slack).

**Bounty:** n8n + Claude Code — Automated Weekly Dev Summary (#5)

---

## ✨ Features

- ⏰ **Weekly cron trigger** — Friday at 5 PM (configurable)
- 📊 **GitHub data** — commits, closed issues, merged PRs (last 7 days)
- 🧠 **Claude AI summary** — `claude-sonnet-4-20250514` generates a narrative report
- 💬 **Discord/Slack delivery** — via webhook
- 🌍 **Multi-language** — English or French (configurable)
- 🛡️ **Robust** — handles empty weeks, API errors, rate limits, large repos (auto-truncation)

## Architecture

```
┌─────────────┐    ┌────────────┐    ┌──────────────────┐
│ Cron Trigger ├──►│ Set Config ├──►│  GitHub API x3    │
│ (Fri 5pm)   │    │ Variables  │    │  (parallel)       │
└─────────────┘    └────────────┘    │  • Commits        │
                                      │  • Closed Issues  │
                                      │  • Merged PRs     │
                                      └────────┬─────────┘
                                               │
                                      ┌────────▼─────────┐
                                      │ Aggregate &      │
                                      │ Format Data      │
                                      └────────┬─────────┘
                                               │
                                      ┌────────▼─────────┐
                                      │ Empty Week?      │
                                      ├────────┬─────────┤
                                  YES │        │ NO
                              ┌───────▼──┐  ┌──▼──────────┐
                              │ Static   │  │ Claude API  │
                              │ Message  │  │ Summarize   │
                              └───────┬──┘  └──┬──────────┘
                                      │        │
                                      │  ┌─────▼──────────┐
                                      │  │ Extract &      │
                                      │  │ Fallback       │
                                      │  └─────┬──────────┘
                                      │        │
                                      ├────────┘
                                      │
                              ┌───────▼──────────┐
                              │ Send to Discord  │
                              └───────┬──────────┘
                                      │
                              ┌───────▼──────────┐
                              │ Log Result       │
                              └──────────────────┘
```

---

## 🚀 Setup (5 Steps)

### Step 1: Install n8n

```bash
# Docker (recommended)
docker run -d --name n8n -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n

# Or npm
npm install -g n8n && n8n start
```

Open `http://localhost:5678` and create an account.

### Step 2: Import the Workflow

1. Open n8n → **Workflows** → **Add Workflow** → **Import from File**
2. Select `weekly-dev-summary.json`
3. The workflow appears with all 11 nodes pre-configured

### Step 3: Configure Credentials

Create **two** HTTP Header Auth credentials in n8n:

| Credential Name | Header Name | Header Value |
|---|---|---|
| `GitHub Token` | `Authorization` | `Bearer ghp_YOUR_GITHUB_TOKEN` |
| `Claude API Key` | `x-api-key` | `sk-ant-YOUR_ANTHROPIC_KEY` |

**To create each:** Settings → Credentials → Add Credential → search "Header Auth" → fill in name/value → Save.

Then assign them to the nodes:
- **Fetch Commits**, **Fetch Closed Issues**, **Fetch Merged PRs** → select `GitHub Token`
- **Claude Summarize** → select `Claude API Key`

> **GitHub token scopes needed:** `repo` (or `public_repo` for public repos only)
>
> **Anthropic API key:** Get one at https://console.anthropic.com/

### Step 4: Set Environment Variables

In n8n, go to **Settings → Environment Variables** (or set in your Docker/system env):

| Variable | Example | Description |
|---|---|---|
| `GITHUB_OWNER` | `n8n-io` | GitHub org or username |
| `GITHUB_REPO` | `n8n` | Repository name |
| `SUMMARY_LANG` | `EN` | `EN` for English, `FR` for French |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Discord webhook URL |

**To get a Discord webhook:** Server Settings → Integrations → Webhooks → New Webhook → Copy URL.

<details>
<summary>📌 Using Slack instead of Discord?</summary>

Edit the **Send to Discord** node's URL to your Slack webhook, and change the JSON body to:
```json
{ "text": "{{ $json.summary }}" }
```
Slack webhooks: https://api.slack.com/messaging/webhooks
</details>

### Step 5: Test & Activate

1. Click **Test Workflow** (▶) to run it immediately
2. Verify each node shows green ✅
3. Check your Discord/Slack channel for the summary
4. Toggle the workflow **Active** (top-right switch) for automatic weekly execution

---

## ⚙️ Configuration Reference

### Schedule
Edit the **Weekly Cron** node to change timing:
- `triggerAtHour`: 0–23 (default: 17 = 5 PM)
- `triggerAtDay`: 1=Mon ... 5=Fri (default: 5)

### Language
Set `SUMMARY_LANG` environment variable:
- `EN` — English (default)
- `FR` — French

### Large Repos
The workflow auto-truncates to 50 commits, 50 issues, and 50 PRs to stay within Claude's context window. The AI is informed when data is truncated.

### Error Handling
- All GitHub API nodes have **3 retries** with 5s backoff
- Claude API has **2 retries** with 10s backoff
- If Claude fails entirely, a **fallback summary** with raw stats is generated
- Empty weeks produce a friendly "no activity" message
- Discord delivery has **2 retries** with 3s backoff

---

## 📁 Files

| File | Description |
|---|---|
| `weekly-dev-summary.json` | n8n workflow (import this) |
| `README.md` | This file |
| `sample-output.md` | Example of what the Discord message looks like |
| `sample-execution.md` | Node-by-node execution log from a test run |

---

## 🔧 Troubleshooting

| Issue | Fix |
|---|---|
| GitHub 401 | Check your token in the GitHub Token credential. Ensure `Bearer ` prefix. |
| GitHub 403 rate limit | Token is rate-limited. Wait or use a different token. The workflow retries automatically. |
| Claude 401 | Check your Anthropic API key in the credential. |
| Claude 529 overloaded | The workflow retries after 10s. If persistent, try again later. |
| Discord 400 | Message too long (>2000 chars). The workflow truncates, but check the Extract node. |
| Empty summary | Check the "Empty Week?" node — your repo may have had no activity. |

---

## License

MIT — use freely, modify as needed.
