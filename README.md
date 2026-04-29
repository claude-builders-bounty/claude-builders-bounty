# Weekly GitHub Summary — n8n Workflow

## Bounty Submission

**[BOUNTY $200] WORKFLOW: n8n + Claude — automated weekly dev summary**

## Files

- `workflows/weekly-github-summary.json` — Importable n8n workflow
- `README.md` — Setup instructions

## Features

- ✅ Weekly cron trigger (Friday 5pm EST, configurable)
- ✅ Fetches commits, closed issues, merged PRs via GitHub API
- ✅ Calls Claude API (`claude-sonnet-4-20250514`) for narrative summary
- ✅ Dual delivery: Discord/Slack webhook OR email
- ✅ Configurable: repo owner/name, branch, language (EN/FR)
- ✅ Smart filtering: excludes merge/chore commits

## Setup

1. Import `workflows/weekly-github-summary.json` into n8n
2. Configure credentials: GitHub API token, Anthropic API key
3. Edit "Set Config & Date Range" node with your repo, language, delivery target
4. Test with **Execute Workflow** button
5. Toggle to **Active** for automated weekly runs

## Architecture

```
Schedule (Fri 5pm) → Config → [Commits + Issues + PRs] → Merge → Claude Prompt → Claude API → [Discord/Slack + Email]
```
