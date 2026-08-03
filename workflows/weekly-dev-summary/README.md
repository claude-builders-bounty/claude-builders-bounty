# Weekly Dev Summary — n8n + Claude API Workflow

## Overview
An n8n workflow that automatically generates a weekly narrative summary of your GitHub repo's activity using the Claude API (claude-sonnet-4-20250514).

## Features
- **🔄 Weekly cron trigger** (Friday 5pm) — fully configurable
- **📊 Fetches from GitHub API**: merged PRs, closed issues, commits for the past week
- **🤖 Calls Claude API** to generate a natural-language narrative summary
- **📨 Delivers via Discord/Slack webhook** (configurable)
- **🌍 Multi-language**: English (default) or French

## Installation (5 Steps)

### Step 1: Import the Workflow
1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `n8n_workflow.json`

### Step 2: Set Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `REPO_URL` | GitHub API URL for your repo | `https://api.github.com/repos/owner/repo` |
| `GITHUB_TOKEN` | GitHub personal access token | `ghp_xxx...` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-xxx...` |
| `DESTINATION` | `discord` or `slack` | `discord` |
| `WEBHOOK_URL` | Discord/Slack webhook URL | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | `EN` or `FR` | `EN` |
| `BRANCH` | Default branch name | `main` |

### Step 3: Configure the Cron Schedule
- Open the **Schedule Trigger** node
- Default: Friday at 5:00 PM
- Adjust as needed in the node settings

### Step 4: Activate the Workflow
1. Click **Save** on the workflow
2. Toggle **Active** to enable scheduled runs

### Step 5: Test
1. Click **Execute Workflow** to run a manual test
2. Check your Discord/Slack channel for the summary

## Output Example
> ### Weekly Dev Summary
> This week saw 12 merged PRs, 8 closed issues, and 34 commits. The team focused on refactoring the authentication module (PRs #89, #92), fixing two critical bugs in the payment pipeline (issues #45, #47), and adding WebSocket support for real-time notifications (PR #95). Project health: stable.

## File Structure
```
n8n_workflow.json   — The importable workflow
README.md          — This file
```

## Requirements
- n8n v1.0+ (self-hosted or cloud)
- GitHub API token (with `repo` scope)
- Anthropic API key
- Discord webhook URL or Slack webhook URL