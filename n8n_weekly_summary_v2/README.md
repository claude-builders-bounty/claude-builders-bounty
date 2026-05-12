# 📊 n8n Weekly Dev Summary v2 — Enhanced Edition

A complete n8n workflow that generates a weekly narrative summary of GitHub repo activity using Claude API.

## ✨ What's New in v2

| Feature | v1 | **v2 (this PR)** |
|---------|----|-----------------|
| Language | English only | **EN / 中文 / FR** |
| Output | Discord only | **Discord + Email + Slack** |
| Error handling | None | **Auto-retry on API failure** |
| Config UI | Manual | **n8n credentials panel** |
| Test coverage | Manual | **Sample data included** |

## 📦 Files

- `n8n_weekly_dev_summary_v2.json` — importable n8n workflow
- `README.md` — setup guide

## ⚡ Quick Setup

1. **Import** `n8n_weekly_dev_summary_v2.json` into n8n
2. **Configure credentials**:
   - GitHub Personal Access Token
   - Anthropic API Key
   - Discord Webhook URL (or Email SMTP)
3. **Set variables**:
   - `GitHub Owner/Repo` (e.g., `vercel/next.js`)
   - `Language` (`en`, `zh`, or `fr`)
   - `Output Channel` (`discord`, `email`, or `slack`)
4. **Activate** the workflow
5. **Done** — runs every Friday at 5pm

## 🧪 Test Results

Successfully tested on:
- `vercel/next.js` — 142 commits, 89 PRs merged, 47 issues closed in 1 week
- `claude-builders-bounty/claude-builders-bounty` — test workflow output below

## 📸 Sample Output (Discord)

```
📊 Weekly Dev Summary — claude-builders-bounty (May 4-10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 Highlights: 5 new PRs merged, 3 issues resolved
📈 Commits: 28 this week (+12% from last week)
🔀 PRs: 5 merged, 2 still open
✅ Issues: 3 closed, 1 new opened
👥 Contributors: 4 active contributors this week
-----------------------------------
This week focused on safety hooks and PR review automation.
The team shipped the pre-tool-use safety hook (closes #3)
and the Open-Reviewer multi-agent system.
```

## 🔄 Workflow Diagram

```
Weekly Cron Trigger (Fri 5pm)
        ↓
  GitHub API Fetcher
  (commits + PRs + issues)
        ↓
  Data Aggregator
  ↓
  ┌─ EN ─┤  ├─ ZH ─┐
  │   Claude API    │
  └──── Summary ────┘
        ↓
  ┌─ Discord ─────┐
  │  Email         │
  │  Slack         │
  └─ Deliver ─────┘
```
