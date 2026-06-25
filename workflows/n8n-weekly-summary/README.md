# n8n + Claude API: Weekly Dev Summary

## Setup
1. Import workflow.json into n8n
2. Set env vars: GITHUB_TOKEN, SUMMARY_EMAIL, OPENAI_API_KEY
3. Runs every Friday at 5pm

## What it does
- Fetches commits, closed issues, merged PRs
- Claude API generates narrative summary
- Emails the formatted report
