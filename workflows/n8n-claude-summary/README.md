# Automated Weekly Dev Summary — n8n + Claude API Workflow

An exportable, zero-code maintenance **n8n workflow** that fetches weekly engineering activity from the GitHub REST API (commits, merged pull requests, closed issues) and uses Anthropic's **Claude 3.5 Sonnet API** to generate a polished weekly narrative report delivered to Discord, Slack, or Email.

---

## Features
- ⏰ **Weekly Cron Trigger**: Runs automatically every Friday at 5:00 PM (`0 17 * * 5`).
- 🐙 **GitHub Multi-Stream Ingestion**: Concurrently queries `/commits`, `/pulls`, and `/issues` for the past 7 days.
- 🧠 **Claude 3.5 Sonnet Integration**: Synthesizes raw commit logs into executive highlights, major features, and stability fixes.
- 🌍 **Configurable Language**: Supports **English (`EN`)** and **French (`FR`)** output summaries.
- 📡 **Multi-Platform Delivery**: Formatted for Discord webhooks, Slack incoming webhooks, or Email.

---

## 5-Step Setup Guide

1. **Import the Workflow**:
   - Open your n8n dashboard.
   - Click **Add Workflow** → **Import from File** and select `workflows/n8n-claude-summary/weekly-dev-summary.json`.

2. **Configure Environment Variables**:
   Set the following variables in your n8n instance or edit the **Configure Workflow Variables** code node:
   - `ANTHROPIC_API_KEY`: Your Anthropic API Key (`sk-ant-...`).
   - `GITHUB_OWNER`: Target GitHub organization / username (e.g. `facebook`).
   - `GITHUB_REPO`: Target GitHub repository name (e.g. `react`).
   - `DISCORD_SLACK_WEBHOOK_URL`: Discord or Slack incoming webhook destination URL.
   - `SUMMARY_LANGUAGE`: `EN` for English, `FR` for French (Default: `EN`).

3. **Test the Aggregation**:
   - Click **Test step** on the *Aggregate Activity & Build Prompt* node to verify commit and PR filtering.

4. **Test Claude Generation**:
   - Click **Test step** on the *Claude API - Generate Narrative* node to verify output formatting.

5. **Activate**:
   - Toggle the workflow switch to **Active** to enable the Friday 5:00 PM schedule.

---

## Sample Delivered Summary

```markdown
🚀 Executive Overview
This week the team focused on hardening API authentication stability and delivering the new Tiered Pricing engine, merging 8 PRs and closing 5 tracking issues.

🌟 Key Highlights & Features Landed
- Tiered Pricing Engine: Implemented 4-tier cost calculation for high-volume API requests (#12028).
- Asynchronous Retry: Added exponential backoff and jitter utility for resilient HTTP calls (#12020).

🐛 Bug Fixes & Stability Improvements
- Multer Upload Error Mapping: Mapped client-side parser errors to 400 Bad Request instead of unhandled 500 errors (#12031).
- Rate Limiting: Enforced IP-based rate limiting on sensitive auth endpoints.

📊 Quick Metrics
- Merged PRs: 8
- Closed Issues: 5
- Total Commits: 24
```
