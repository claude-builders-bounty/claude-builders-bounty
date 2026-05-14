# n8n Weekly Dev Summary Workflow 🤖

Automatically generates a weekly narrative summary of your GitHub repo's activity using Claude AI.

## Features

- ⏰ **Runs weekly** (every Monday 9AM) via Schedule Trigger
- 📊 **Fetches** commits, PRs, and closed issues from the past week
- 🤖 **Analyzes** with Claude API (Haiku — fast & cheap)
- 📝 **Generates** a narrative Markdown summary
- 💬 **Sends** to Slack (or saves locally)
- 📁 **Saves** a `.md` file per week

## How to Import

1. Open n8n (self-hosted or cloud.n8n.io)
2. Go to **Workflows → Import from File**
3. Select `n8n-weekly-dev-summary.json`
4. Configure credentials (see below)

## Required Credentials

| Credential | Type | Description |
|-----------|------|-------------|
| GitHub API | HTTP Header Auth | Token with `repo` scope |
| Claude API | HTTP Header Auth | Anthropic API key (get at console.anthropic.com) |
| Slack Webhook | Webhook URL | Optional — webhook URL for Slack channel |

### Setting up Credentials

**GitHub Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Generate with `repo` and `public_repo` scopes
3. In n8n, create a "Header Auth" credential with header name `Authorization` and value `Bearer YOUR_TOKEN`

**Claude API Key:**
1. Go to https://console.anthropic.com/ and create an API key
2. In n8n, create a "Header Auth" credential

**Slack Webhook (optional):**
1. Go to Slack API → Incoming Webhooks
2. Create a webhook for your channel
3. Enter the URL in the workflow webhook node

## Configuration

After importing, edit the **Fetch Commits/PRs/Issues** nodes:
- Change the URL from `https://api.github.com/repos/owner/repo` to your actual repo

Or set it as a workflow variable for easy reuse.

## Output Example

```
## 📊 Weekly Dev Summary — 2026-05-11 to 2026-05-17

### Weekly Overview
This week focused on improving CI pipeline reliability...

### Key Changes
- Fixed flaky test suite in CI (#42)
- Added rate limiting to API endpoints (#45)
- Updated dependencies to latest versions

### Issues Resolved
- #38: Memory leak in WebSocket handler
- #41: Login timeout on mobile devices

### Looking Ahead
- Database migration v2 planning
- Performance audit scheduled
```

## Cost Estimate

Per run: ~2,000 Claude Haiku tokens ≈ **$0.01-0.02**
Weekly cost: ~$0.05/month

## Bounty

This workflow was created for **Bounty #5 ($200)** at claude-builders-bounty.
