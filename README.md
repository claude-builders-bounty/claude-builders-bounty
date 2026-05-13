# Weekly Dev Summary — n8n + Claude

> **Bounty: $200** — Automated weekly development summary workflow

## Overview

This n8n workflow automatically generates a narrative weekly summary of any GitHub repository's activity using Claude API.

**What it does:**
1. Runs every Friday at 5 PM (cron)
2. Fetches commits, closed issues, and merged PRs from any GitHub repo
3. Calls Claude Sonnet to generate a narrative summary
4. Delivers via **Email** and/or **Slack/Discord webhook**
5. Supports **EN** and **FR** languages

## Quick Start (5 Steps)

### 1. Import the workflow
- Open n8n → **Workflows** → **Import from File**
- Select `n8n_workflow.json`

### 2. Set up credentials

Create these credentials in n8n:
| Credential | Type | Fields |
|------------|------|--------|
| `github-credentials` | Header Auth | Key: `Authorization`, Value: `Bearer YOUR_GITHUB_TOKEN` |
| `claude-credentials` | Header Auth | Key: `x-api-key`, Value: `YOUR_CLAUDE_API_KEY` |

### 3. Configure environment variables

Set these in n8n → **Settings** → **Environment Variables**:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_REPO_DEFAULT` | ✅ Yes | — | e.g. `anthropics/claude-code` |
| `SUMMARY_LANGUAGE` | No | `EN` | `EN` or `FR` |
| `EMAIL_TO` | For email | — | Recipient email address |
| `EMAIL_FROM` | For email | `summary@devweekly.com` | Sender email |
| `WEBHOOK_URL` | For webhook | — | Slack/Discord webhook URL |

### 4. Activate the workflow
- Toggle **Active** to enable the weekly cron trigger
- Or run manually to test

### 5. Test
- Click **Execute Workflow**
- Verify the output in your email or Slack channel

## Files

| File | Description |
|------|-------------|
| `n8n_workflow.json` | Importable n8n workflow |
| `python_version.py` | Standalone Python version (no n8n needed) |

## Language Support

Set `SUMMARY_LANGUAGE` to `EN` (English) or `FR` (French).

## Screenshots

*(Insert screenshot of successful execution here)*

---

*Built for [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty)*
