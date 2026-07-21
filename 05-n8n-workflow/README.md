# n8n + Claude AI — Weekly Dev Summary

An n8n workflow that auto-generates a weekly narrative summary of GitHub repo activity using the Claude API.

## Setup (5 Steps)

1. **Import into n8n**: Copy `weekly-dev-summary.json` → n8n → Import Workflow
2. **Configure variables** in the "Set Config" node:
   - `repo_owner` / `repo_name` — target GitHub repo
   - `github_token` — GitHub personal access token (read: repo)
   - `anthropic_api_key` — Claude API key
   - `webhook_url` — Discord/Slack webhook URL OR SMTP settings
   - `language` — `EN` for English, `FR` for French
3. **Connect the trigger**: Wire "Set Config" → "Friday 5pm Trigger"
4. **Test**: Click "Execute Workflow" to test manually
5. **Activate**: Toggle the workflow Active switch

## How It Works

```
Friday 5pm → Fetch commits/issues/PRs from GitHub API
           → Build structured prompt for Claude
           → Claude generates narrative summary
           → Deliver via Discord/Slack webhook or email
```

## What You Get

Every Friday at 5pm, your team receives:

```markdown
# 📊 Weekly Dev Summary: myorg/myrepo
> 2026-07-12 → 2026-07-19

## Overview
This week focused on improving authentication flows and fixing performance issues.

## What Changed
The team shipped 23 commits across 8 files. Key additions include OAuth2 provider support
and rate limiting middleware. Performance optimizations reduced API response times by 40%.

## Issues Resolved
- #142: Fix login redirect loop (closed by @alice)
- #138: Add password reset flow (closed by @bob)
...
```

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token with `repo` scope
- Anthropic API key (Claude Sonnet 4)
- Discord/Slack webhook OR SMTP server for delivery

## Customization

- **Cron schedule**: Edit the "Friday 5pm Trigger" node → change the cron expression
- **Language**: Set `language` variable to `EN` or `FR`
- **Summary depth**: Edit the prompt in "Build Claude Prompt" node
- **Delivery**: Use Discord, Slack, email, or add any n8n output node
