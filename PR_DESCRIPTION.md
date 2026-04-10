## Summary

Complete implementation of the n8n workflow for automated weekly GitHub repository summaries using Claude API.

## What's Included

### Files
- `workflows/weekly-dev-summary/weekly-dev-summary-workflow.json` - Exportable n8n workflow
- `workflows/weekly-dev-summary/README.md` - Complete setup instructions

### Features
- Weekly cron trigger (Friday 5PM by default, customizable)
- GitHub API integration - fetches commits, closed issues, merged PRs
- Claude API integration - generates narrative summaries
- Multiple output channels - Discord, Slack, or email
- Configurable variables - GitHub repo, channel, language (EN/FR)
- 5-step setup - README has complete instructions

## Setup Requirements

1. n8n instance (self-hosted or cloud)
2. GitHub personal access token
3. Claude API key
4. Discord webhook OR Slack token OR SMTP settings

## Acceptance Criteria

- [x] Exportable n8n workflow (.json file)
- [x] Trigger: weekly cron (Friday 5PM)
- [x] Fetches GitHub API: commits, closed issues, merged PRs
- [x] Calls Claude API (claude-sonnet-4-20250514)
- [x] Delivers via Discord/Slack/email
- [x] Configurable variables: repo, channel, language
- [x] README with 5-step setup

## Bounty Claim

This PR addresses issue #5.

/opire try

Closes #5