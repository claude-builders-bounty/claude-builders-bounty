# Automated Weekly GitHub Dev Summary (n8n + Claude API) 📊

> Production n8n workflow that fetches GitHub repository activity (commits, closed issues, merged PRs) for the past 7 days and uses the Claude Messages API to generate a narrative executive digest delivered directly to Discord or Slack.

[![Bounty](https://img.shields.io/badge/bounty-%24200-success)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)
[![n8n](https://img.shields.io/badge/n8n-importable%20workflow-orange)](github_weekly_summary.json)

---

## ⚡ 5-Step Setup Guide

1. **Import Workflow**:
   In your n8n workspace, navigate to **Workflows** → **Import from File** and select [`github_weekly_summary.json`](github_weekly_summary.json).
2. **Configure Anthropic API Key**:
   Set `ANTHROPIC_API_KEY` in your n8n environment variables, or paste your API key into the `Generate Narrative via Claude API` HTTP Request header (`x-api-key`).
3. **Configure Repository & Destination**:
   Double-click the **Set Configuration** node and update:
   - `repo_owner`: Target GitHub organization / user (e.g. `anthropics`)
   - `repo_name`: Target repository name (e.g. `anthropic-quickstarts`)
   - `summary_language`: Set to `EN` (English) or `FR` (French)
   - `webhook_url`: Discord or Slack incoming webhook endpoint
4. **Test Run**:
   Click **Test step** on the *Weekly Schedule* trigger to verify data ingestion and dispatch.
5. **Activate**:
   Toggle the workflow status to **Active**. It will automatically trigger every Friday at 5:00 PM.

---

## 🏗️ Workflow Architecture

```text
[Weekly Cron (Fri 5PM)]
       │
       ▼
[Set Config (Repo, Lang, Webhook)]
       │
       ▼
[Calculate 7-Day Window]
       │
  ┌────┼──────────────┐
  ▼    ▼              ▼
[Commits] [Closed Issues] [Merged PRs]
  └────┬──────────────┘
       ▼
[Aggregate Data & Construct Claude Prompt]
       │
       ▼
[Call Claude API (claude-3-7-sonnet)]
       │
       ▼
[Dispatch Narrative to Discord / Slack Webhook]
```

---

## 📄 Sample Output (Discord / Slack)

```markdown
🚀 **Weekly Engineering Digest: anthropics/anthropic-quickstarts**

### 🌟 Executive Momentum
The team delivered substantial progress over the past 7 days, successfully merging 8 pull requests and closing 6 community issues with major focus on tool-use reliability and streaming optimizations.

### 🚢 Major Shipments & Highlights
- **Streaming Response Optimization**: Refactored SSE buffer handlers to reduce latency by 24%.
- **Computer-Use SDK Example**: Released comprehensive end-to-end OS automation tutorial with Docker sandbox support.

### 🐛 Bug Fixes & Refactors
- Fixed token accounting bug in multi-turn tool calling loop (#142).
- Resolved race condition in concurrent prompt caching eviction.

### 👏 Contributor Shoutouts
Special thanks to @alex, @elena-dev, and @samuel for impactful community contributions this week!
```
