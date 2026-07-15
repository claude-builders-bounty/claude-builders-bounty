# n8n + Claude API - Automated Weekly Dev Summary

Weekly development summary automation using n8n and Claude API.

## Overview

This workflow automatically generates a weekly development summary by:
1. Fetching GitHub activity (commits, issues, PRs)
2. Summarizing the data
3. Sending to Claude API for natural language generation
4. Posting the formatted summary to Slack

## Workflow Steps

```
Start → Calculate Week Range → Fetch GitHub Data → Summarize → Claude API → Slack
                                          ↓
                                    Save Report
```

## Prerequisites

- n8n instance (cloud or self-hosted)
- GitHub API credentials
- Anthropic Claude API key
- Slack workspace with bot integration

## Setup

### 1. Import the Workflow

```bash
# In n8n, go to Workflows → Import from File
# Select: weekly-dev-summary.json
```

### 2. Configure Credentials

Create credentials in n8n:

**GitHub API**
- Name: `github-api`
- Token: Your GitHub Personal Access Token

**Claude API**
- Name: `claude-api`
- API Key: Your Anthropic API key

**Slack API**
- Name: `slack-api`
- Token: Your Slack Bot Token

### 3. Set Environment Variables

In n8n Settings → Variables:

```
GITHUB_OWNER=your-org-or-username
GITHUB_REPO=your-repo-name
SLACK_CHANNEL=#dev-updates
```

### 4. Schedule the Workflow

Add a Schedule Trigger node to run weekly (e.g., every Monday at 9 AM).

## Workflow Nodes

| Node | Purpose |
|------|---------|
| Calculate Week Range | Determine last 7 days |
| Get GitHub Commits | Fetch recent commits |
| Get GitHub Issues | Fetch opened/closed issues |
| Get GitHub PRs | Fetch opened/merged PRs |
| Summarize Activity | Process and count data |
| Claude API | Generate natural language summary |
| Send to Slack | Post to channel |
| Save Report | Archive JSON report |

## Bounty

Part of [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) #5 ($200)
