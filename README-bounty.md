# n8n Weekly GitHub Dev Summary

A complete n8n workflow that automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API.

## What It Does

Every Friday at 5 PM, this workflow:
1. 📊 Fetches **commits**, **closed issues**, and **merged PRs** from your GitHub repo
2. 🧠 Sends the data to **Claude Sonnet 4** to generate a professional narrative summary
3. 📧 Emails the report to your team

## Setup

### Prerequisites
- n8n instance (self-hosted or cloud)
- Claude API key
- GitHub Personal Access Token (with repo scope)
- SMTP credentials

### Import
1. Open n8n → Import → select `weekly-report-n8n.json`
2. Fill in the required credentials:
   - GitHub token
   - Anthropic API key
   - SMTP settings (from email, to email)

### Configuration (n8n Workflow Static Data)
Set the following in the Cron node or as workflow-level static data:
```json
{
  "repo_owner": "your-org",
  "repo_name": "your-repo",
  "since_date": "2024-01-01T00:00:00Z",
  "week_label": "Jan 1 - Jan 7",
  "report_recipients": "team@company.com",
  "smtp_from": "reports@company.com",
  "github_token": "ghp_xxx",
  "anthropic_api_key": "sk-ant-xxx"
}
```

## Workflow Architecture

```
Cron (Fri 5PM)
  ├── Fetch Commits ──┐
  ├── Fetch Issues ───┼── Merge Data ── Claude API ── Send Email
  └── Fetch PRs ──────┘
```

## Files

- `weekly-report-n8n.json` — Importable n8n workflow file

## Bounty

This workflow was created for [Claude Builders Bounty #5 ($200)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)
