# GitHub Weekly Dev Summary — n8n Workflow

Automatically generate a narrative summary of your GitHub repo's weekly activity using Claude API.

## Features

- ⏰ **Weekly cron** (Friday 5pm) — fully automated
- 📊 Fetches: commits, closed issues, merged PRs from the past 7 days
- 🤖 Generates a professional narrative summary via Claude API (`claude-sonnet-4-20250514`)
- 📧 Delivers via email (configurable)
- 🌐 Supports EN/FR language
- 🔧 Fully configurable via environment variables

## Setup (5 Steps)

1. **Install n8n**: `npx n8n start` or `docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n`

2. **Import the workflow**: Settings → Import → Select `github_weekly_summary.json`

3. **Set environment variables** in n8n:
   - `GITHUB_TOKEN` — GitHub personal access token
   - `GITHUB_OWNER` — repo owner (e.g., `your-org`)
   - `GITHUB_REPO` — repo name (e.g., `your-project`)
   - `CLAUDE_API_KEY` — Anthropic API key
   - `EMAIL_TO` — recipient email
   - `EMAIL_FROM` — sender email (optional)

4. **Test the workflow**: Click "Execute Workflow" — verify output

5. **Activate**: Toggle "Active" to enable weekly schedule

## Output Example

> *"This week saw significant progress on the authentication module with 12 commits, 3 closed issues, and 2 merged PRs. Key highlights include..."*

## Files

- `github_weekly_summary.json` — importable n8n workflow
- `README.md` — this file
