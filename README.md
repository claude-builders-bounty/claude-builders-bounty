# Weekly Dev Summary — n8n Workflow

Automated weekly narrative summary of GitHub repo activity using Claude API.

## Setup (5 Steps)

1. **Import workflow** — In n8n, go to Workflows → Import → select `weekly-dev-summary-workflow.json`
2. **Add credentials** — Create two Generic Credentials:
   - `githubToken` — GitHub Personal Access Token (repo scope)
   - `anthropicApiKey` — Anthropic API key (or use 9router at `http://localhost:20128/v1`)
3. **Configure variables** — Open workflow, click "Weekly Cron" node, set:
   - `githubRepo` — e.g. `https://api.github.com/repos/owner/repo/commits`
   - `githubToken` — your credential name
   - `discordWebhook` — Discord webhook URL (or use email node instead)
   - `language` — `EN` or `FR`
4. **Test run** — Click "Execute Workflow" → verify Discord receives summary
5. **Activate** — Toggle "Active" on workflow → runs every Friday 5pm automatically

## Requirements

- n8n (self-hosted or cloud)
- GitHub PAT with `repo` scope
- Anthropic API key (or compatible endpoint like 9router)
- Discord webhook URL (or SMTP for email)

## Files

- `weekly-dev-summary-workflow.json` — importable n8n workflow
- `README.md` — this file

## Testing

```bash
# Run n8n locally (if not running)
n8n start

# Import via CLI
n8n import:workflow --input=weekly-dev-summary-workflow.json
```

## Acceptance Criteria Met

- �� Exportable `.json` workflow
- �� Weekly cron trigger (Friday 5pm)
- �� Fetches commits, closed issues, merged PRs from GitHub API
- �� Calls Claude API (`claude-sonnet-4-20250514`)
- �� Delivers via Discord webhook (configurable)
- �� Configurable variables: repo, channel, language
- �� README with 5-step setup