# 🚀 n8n + Claude Automated Weekly Dev Summary

> **Production n8n Workflow Package** for generating high-impact, autonomous weekly executive dev summaries from GitHub activity using the Claude API (`claude-sonnet-4-20250514` / `claude-3-5-sonnet-20241022`).
> **Bounty Target:** Issue #5 ($200 USD) on `claude-builders-bounty/claude-builders-bounty` (Powered by Opire).

---

## 🌟 Overview & Architecture

This workflow automates the entire weekly engineering reporting lifecycle:
1. **Schedule Trigger:** Triggers autonomously every Friday at 5:00 PM UTC (`0 17 * * 5`).
2. **GitHub Activity Fetching:** Fetches all commits, closed PRs (filtering strictly merged PRs), and resolved issues over the configured lookback window (default: 7 days).
3. **Data Aggregation & Normalization:** Extracts author handles, PR labels, commit hashes, and issue titles.
4. **Claude AI Narrative Generation:** Calls Claude Sonnet via Anthropic Messages API with a structured prompt to produce a multi-section executive digest in English or French.
5. **Multi-Channel Delivery:** Dynamically formats and routes beautiful rich embeds to **Discord**, formatted blocks to **Slack**, or webhooks/email.

```
[Cron: Friday 17:00] ──> [Config & Date Calc] ──> [GitHub Commits / PRs / Issues]
                                                           │
                                                           ▼
[Discord / Slack] <── [Payload Formatter] <── [Claude Sonnet API] <── [Activity Aggregator]
```

---

## ⚡ 5-Step Setup Guide

### 1. Import Workflow into n8n
1. Open your n8n dashboard (Cloud or Self-Hosted).
2. Go to **Workflows** > **Import from File...**
3. Select `workflows/weekly_dev_summary_n8n.json`.

### 2. Configure Environment Variables
Set the following variables in your n8n instance or in the **Config & Environment** node:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `GITHUB_OWNER` | GitHub organization or username | `ubiquity` / `my-org` |
| `GITHUB_REPO` | GitHub repository name | `ubiquity-dollar` / `my-repo` |
| `SUMMARY_LANGUAGE` | Output language (`EN` or `FR`) | `EN` |
| `DELIVERY_CHANNEL` | Target platform (`discord` or `slack`) | `discord` |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL for posting embeds | `https://discord.com/api/webhooks/...` |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | `https://hooks.slack.com/services/...` |
| `ANTHROPIC_API_KEY` | Anthropic API Key for Claude | `sk-ant-...` |
| `CLAUDE_MODEL` | Claude model identifier | `claude-sonnet-4-20250514` |

### 3. Set Up GitHub Credentials (Optional for Higher Rate Limits)
In the HTTP Request nodes (`Fetch Weekly Commits`, `Fetch Closed PRs`, `Fetch Closed Issues`), attach your GitHub Personal Access Token (`Bearer ghp_...`) to avoid unauthenticated rate limits (60 req/hr -> 5,000 req/hr).

### 4. Test the Workflow
Click **Test step** or **Execute Workflow** in n8n. The nodes will execute sequentially and publish the digest to your configured channel.

### 5. Activate Schedule
Toggle the workflow switch to **Active**. The cron trigger will run every Friday at 17:00 UTC.

---

## 🧪 Local Verification & Tests

Run the automated test suite locally:

```bash
# Run schema and logic unit tests
python3 -m unittest discover -s tests/

# Run end-to-end simulation
python3 scripts/simulate_pipeline.py
```

---

## 📋 Acceptance Criteria Checklist
- [x] **Exportable n8n workflow (`.json` file):** `workflows/weekly_dev_summary_n8n.json`
- [x] **Trigger:** Weekly cron (`0 17 * * 5` - Friday 5pm)
- [x] **GitHub API extraction:** Commits, closed issues, merged PRs in 7-day window
- [x] **Claude API integration:** `claude-sonnet-4-20250514` via Anthropic Messages API
- [x] **Delivery options:** Discord embeds & Slack Block Kit payloads
- [x] **Configurable variables:** Repo owner/name, delivery channel, language (`EN`/`FR`)
- [x] **Test suite & sample outputs:** Included in `tests/` and `sample_outputs/`
- [x] **Clean 5-step README documentation**
