# n8n + Claude Code Weekly Dev Summary

An exportable n8n workflow that automatically generates a weekly narrative summary of GitHub repo activity using the Claude API.

## Features
- Weekly cron trigger (Friday at 5pm, configurable)
- Fetches GitHub data: commits, closed issues, merged PRs for the week
- Claude-generated narrative: structured Markdown summary
- Discord delivery: posts to any webhook URL
- Configurable: repo, language (EN/FR), all via env vars

## Installation
1. Import weekly-dev-summary.json into n8n
2. Set environment variables:
   GITHUB_TOKEN, CLAUDE_API_KEY, DISCORD_WEBHOOK, GITHUB_REPO
3. Activate the workflow

## Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| GITHUB_REPO | owner/repo | Repository to monitor |
| SUMMARY_LANGUAGE | EN | Output language (EN/FR/CN) |
| DISCORD_WEBHOOK | (required) | Discord webhook URL |
| GITHUB_TOKEN | (required) | GitHub personal access token |
| CLAUDE_API_KEY | (required) | Anthropic Claude API key |

## Output Format
The weekly summary includes:
1. Highlights - Top achievements
2. Code Changes - Major areas of work
3. Issues and Fixes - Bugs fixed
4. Looking Ahead - What is coming next

## Tested
Successfully tested on a real n8n instance.
