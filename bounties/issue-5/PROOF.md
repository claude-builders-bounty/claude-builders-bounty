# Issue #5 — n8n Weekly Dev Summary Workflow

Delivery for [claude-builders-bounty#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5).

## What was implemented

A complete n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

| File | Purpose |
|------|---------|
| `workflows/weekly-dev-summary.json` | Exportable n8n workflow (importable) |
| `workflows/README.md` | Setup instructions (5 steps) |

## Workflow steps

1. **Cron trigger** — Every Friday at 5pm
2. **GitHub API** — Fetches commits, closed issues, merged PRs for the past week
3. **Claude API** — Generates narrative summary (`claude-sonnet-4-20250514`)
4. **Delivery** — Sends summary via Discord webhook (configurable)

## Configurable variables

| Variable | Description |
|----------|-------------|
| `GITHUB_REPO` | Owner/repo to summarize |
| `DISCORD_WEBHOOK_URL` | Delivery destination |
| `LANGUAGE` | Summary language (EN/FR) |
| `CLAUDE_API_KEY` | Claude API key |

## Setup (5 steps)

1. Import `workflows/weekly-dev-summary.json` into n8n
2. Set environment variables: `GITHUB_REPO`, `DISCORD_WEBHOOK_URL`, `CLAUDE_API_KEY`
3. Set `LANGUAGE` to `EN` or `FR`
4. Activate the workflow
5. Test with manual trigger

## Verification

```bash
python3 build.py
# All checks pass — workflow JSON is valid
```

The workflow JSON was validated against n8n's schema and tested for import compatibility.

Closes #5
