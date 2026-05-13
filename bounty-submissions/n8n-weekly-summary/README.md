# n8n + Claude Code — Automated Weekly Dev Summary
> **Bounty $200**


## Overview

A complete n8n workflow that automatically generates a weekly narrative summary
of a GitHub repository's activity using the Claude (Anthropic) API for AI-powered
narrative generation.

Triggers every **Friday at 5pm UTC** (configurable cron).

## What It Does

1. 🔍 **Fetches** commits, issues, PRs, and releases from GitHub API (last 7 days)
2. 📊 **Aggregates** activity data (contributors, merged PRs, closed issues, new issues)
3. 🤖 **Generates** a narrative summary via Claude API (300-500 word Markdown report)
4. 📬 **Delivers** via email + optional Slack post + optional GitHub issue

## 🌐 Multi-Language Support

The workflow supports English (EN) and French (FR) out of the box.

**How to switch language:**

```bash
# English (default)
export SUMMARY_LANG=EN

# French
export SUMMARY_LANG=FR
```

Set the `SUMMARY_LANG` environment variable in your n8n instance:
- **n8n Cloud**: Settings → Environment Variables → Add `SUMMARY_LANG=FR`
- **Self-hosted**: Add to `.env` or `docker-compose.yml`

The "Build Claude Prompt" Code Node uses this variable to inject the correct
language instruction into the prompt sent to Claude API.

## 📸 Execution Verification

> _Real screenshots will be updated upon final deployment with active API credentials._

**Execution flow description:**

When deployed on a live n8n instance, the workflow runs as follows:

1. **Schedule Trigger** activates at the configured cron time (Friday 5pm).
2. **Set Repository Config** initializes the target GitHub repo URL.
3. Four parallel **HTTP Request nodes** simultaneously fetch commits, issues, PRs, and releases from the GitHub API — each with Bearer token authentication and 30-second timeout.
4. **Merge node** combines all four API responses into a single dataset by position.
5. **Aggregate Code node** transforms raw JSON into structured statistics: commit count, unique contributors, merged/closed/open PR counts, issue summaries.
6. **Build Claude Prompt node** constructs a detailed prompt including the aggregated stats, recent commits, and the language instruction resolved from the `SUMMARY_LANG` environment variable.
7. **Claude API node** sends the prompt to `api.anthropic.com/v1/messages` (model: `claude-sonnet-4-20250514`), receiving a narrative Markdown summary.
8. **Format Final Report node** assembles the complete Markdown report with repo name, date range, and AI-generated content.
9. Three parallel **delivery nodes** distribute the report via email (SMTP), Slack webhook, and an optional GitHub issue — each independently configurable.

**Validated locally (2026-05-13):** Workflow JSON imports cleanly. Multi-language switching (`SUMMARY_LANG=FR`) verified in the Build Prompt node output. All GitHub API nodes configured with env-var-based auth. See [EXECUTION_LOG.md](./EXECUTION_LOG.md) for detailed trace.

## Installation

### 1. Import into n8n
```
n8n → Workflows → Import from File → weekly-dev-summary.json
```

### 2. Set Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | ✅ Yes | GitHub Personal Access Token (repo scope) |
| `ANTHROPIC_API_KEY` | ✅ Yes | Anthropic API key for Claude |
| `NOTIFY_EMAIL` | ⚠️ Recommended | Where to send the report |
| `SMTP_FROM` | ⚠️ Recommended | Sender email (for email node) |
| `SLACK_WEBHOOK_URL` | Optional | Slack incoming webhook |
| `SUMMARY_LANG` | Optional | Language: EN (default) or FR |
| `REPO_NAME` | Optional | Override repo display name |

### 3. Configure Repository
Edit the **"Set Repository Config"** node:
- `repo_name`: your `owner/repo`
- `repo_api_url`: your `https://api.github.com/repos/owner/repo`

### 4. Configure Email/Slack (optional)
- **Email**: Set up SMTP credentials in n8n → Credentials
- **Slack**: Set `SLACK_WEBHOOK_URL` env var

## Workflow Architecture

```
┌─────────────────┐
│ Weekly Cron      │  Friday 5pm UTC
│ (Schedule)       │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Set Repo │  owner/repo → repo_api_url
    └────┬────┘
         │
    ┌────▼────────────────────────────────┐
    │ Parallel API Calls (GitHub API)      │
    │ ├─ Fetch Commits (since 7d)          │
    │ ├─ Fetch Issues (updated 7d)         │
    │ ├─ Fetch PRs (all, sorted)           │
    │ └─ Fetch Releases (latest 5)         │
    └────┬────────────────────────────────┘
         │
    ┌────▼────┐
    │ Merge    │  Combine all 4 API responses
    └────┬────┘
         │
    ┌────▼────────────┐
    │ Aggregate &       │  JS: summarize commits, 
    │ Summarize         │  filter issues/PRs, stats
    └────┬────────────┘
         │
    ┌────▼────────────┐
    │ Build Claude      │  JS: construct detailed
    │ Prompt            │  prompt from aggregated data
    └────┬────────────┘
         │
    ┌────▼────────────┐
    │ Claude API        │  POST /v1/messages
    │ (Anthropic)       │  Generate narrative
    └────┬────────────┘
         │
    ┌────▼────────────┐
    │ Format Final      │  Assemble full Markdown
    │ Report            │  report with metadata
    └────┬────────────┘
         │
    ┌────▼──────────────────────────────┐
    │ Delivery (parallel)                │
    │ ├─ Send Email                      │
    │ ├─ Post to Slack (optional)        │
    │ └─ Create GitHub Issue (optional)  │
    └───────────────────────────────────┘
```

## Sample Output

```markdown
# 📊 Weekly Dev Summary: acme/saas-app

**2026-05-05 → 2026-05-12**

## 🚀 What Shipped
This week we landed the new onboarding flow (#234 by @alice) and shipped
v2.1.0 with the redesigned analytics dashboard. The team also completed
the migration from REST to tRPC, which cut API latency by 40%.

## 🔧 What We Fixed
- Resolved the Stripe webhook timeout (#231) — payments now process under 2s
- Fixed dark mode flicker on page load (#228)
- Patched a security vulnerability in the file upload handler

## 👥 Contributors
Shout-out to @alice, @bob, @charlie, and @diana for 47 commits this week!

## 📊 By the Numbers
| Metric | Count |
|--------|-------|
| Commits | 47 |
| Contributors | 4 |
| PRs Merged | 7 |
| Issues Closed | 5 |
| New Issues | 3 |
| Latest Release | v2.1.0 |

## 🔮 What's Next
@bob is working on the team billing feature (#242), and @charlie has
started the end-to-end test suite. The P0 bug in search indexing (#239)
is on deck for next week.
```

## Environment Variables Reference

```bash
# Required
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxx"

# Delivery
export NOTIFY_EMAIL="team@acme.com"
export SMTP_FROM="dev-summary@acme.com"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx"

# Optional
export REPO_NAME="acme/saas-app"
```

## Cost Estimate

- Claude API (Sonnet): ~$0.01-0.02 per weekly run (2K output tokens)
- n8n: Free (self-hosted) or cloud plan
- **Total: <$1/month for weekly reports**

--- 
