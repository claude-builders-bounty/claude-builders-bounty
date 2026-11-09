# n8n + Claude Code Weekly Dev Summary Agent

A Claude Code skill that generates a weekly development summary from git history and sends it via n8n webhook.

## Usage

```
/weekly-dev-summary --webhook-url <n8n-webhook-url> [--days 7] [--post]
```

Or standalone:

```bash
node weekly-dev-summary.js --webhook-url https://n8n.example.com/webhook/weekly-summary --days 7
```

## What it does

1. Fetches git commits from the last N days (default 7)
2. Categorizes commits by type (feat/fix/docs/refactor/test/chore)
3. Identifies top contributors by commit count
4. Lists merged PRs (if GitHub token provided)
5. Generates a formatted summary markdown
6. Posts to n8n webhook URL for distribution (Slack, Discord, Email, etc.)

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill definition |
| `weekly-dev-summary.js` | Node.js script (zero dependencies) |
| `README.md` | Installation and n8n setup guide |
| `test-weekly.js` | Test suite with synthetic git data |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | No | GitHub PAT for PR metadata (enhances summary) |
| `N8N_WEBHOOK_URL` | No | n8n webhook URL (can also pass via --webhook-url) |

## Example Output

```
# Weekly Dev Summary — Oct 28 to Nov 3, 2026

## Overview
- 47 commits across 12 files
- 4 contributors
- 3 merged PRs

## Commits by Type
- 🚀 Added: 18 (38%)
- 🐛 Fixed: 12 (26%)
- 📝 Changed: 10 (21%)
- 🧹 Chore: 7 (15%)

## Top Contributors
- @alice — 23 commits
- @bob — 15 commits
- @charlie — 9 commits

## Merged PRs
- #1242: Add user authentication flow (@alice)
- #1238: Fix login redirect bug (@bob)
- #1235: Update dependencies (@charlie)

## Notable Changes
- Implemented dark mode toggle across all pages
- Added rate limiting to login endpoint
- Migrated from REST to GraphQL for user profile
```

## n8n Setup

1. Create a new n8n workflow with a **Webhook** trigger node
2. Set HTTP Method to POST
3. Copy the webhook URL
4. Add downstream nodes (Slack, Discord, Email, etc.)
5. Run the agent with `--webhook-url <your-webhook-url> --post`

## Requirements

- Node.js 18+
- Git repository with commit history
- n8n instance with webhook endpoint (for posting)

## Test

```bash
node test-weekly.js
```

Creates a temp repo with synthetic commits and verifies the summary generation.
