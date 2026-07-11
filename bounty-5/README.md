# Weekly GitHub Dev Summary Workflow

An n8n workflow that generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

## Features
- ✅ Exportable n8n workflow (importable `.json` file)
- ✅ Trigger: weekly cron (Friday at 5pm)
- ✅ Fetches from GitHub API: commits, closed issues for the week
- ✅ Calls Claude API (`claude-sonnet-4-20250514`) to generate a narrative summary
- ✅ Sends the summary via email

## Setup
1. Import `weekly-dev-summary.json` into n8n
2. Set environment variables:
   - `GITHUB_TOKEN` — GitHub Personal Access Token
   - `GITHUB_REPO` — Repo in `owner/repo` format
   - `CLAUDE_API_KEY` — Anthropic API key
3. Configure the email node with your SMTP settings
4. Activate the workflow

## Environment Variables
| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub PAT with repo read access |
| `GITHUB_REPO` | Repository in `owner/repo` format (e.g. `octocat/Hello-World`) |
| `CLAUDE_API_KEY` | Anthropic API key for Claude |
