# n8n + Claude Code: Weekly Dev Summary Workflow

## Overview
Automated n8n workflow that triggers weekly on Friday at 5 PM, fetches GitHub commits, closed issues, and merged PRs, summarizes them via Claude API, and delivers the report to Discord and Email.

## 5-Step Setup
1. Import `n8n-workflow.json` into your n8n instance.
2. Configure GitHub OAuth2 credentials in n8n.
3. Configure Anthropic API credentials for Claude.
4. Set environment variable `DISCORD_WEBHOOK_URL` and email settings.
5. Toggle workflow to **Active**.

## Testing
After activation, run manually once to verify:
- GitHub data fetched
- Claude summary generated
- Discord/Email delivered

## Requirements
- n8n instance (self-hosted or cloud)
- GitHub OAuth2 app with repo access
- Anthropic API key (Claude Sonnet 4)
- Discord webhook or SMTP for email