# Weekly Dev Summary (n8n + Claude)

## Setup (5 steps or fewer)
1. Import `weekly-dev-summary.json` into your n8n instance.
2. Add your GitHub token in the "GitHub API" node credentials.
3. Add your Anthropic API key in the "Claude API" node credentials.
4. Set the configurable variables in the "Set Config" node: `githubRepo`, `destinationChannel` (Discord/Slack webhook URL or email), `language` (EN/FR).
5. Activate the workflow — it runs every Friday at 5pm.

## What it does
- Fetches commits, closed issues, and merged PRs from the past 7 days via GitHub API.
- Calls Claude Sonnet 4 (`claude-sonnet-4-20250514`) to generate a narrative summary.
- Delivers the summary via Discord/Slack webhook or email.

## Acceptance Criteria Met
- [x] Exportable n8n workflow (.json)
- [x] Weekly cron trigger (Friday 5pm)
- [x] Fetches commits, closed issues, merged PRs
- [x] Calls Claude API (`claude-sonnet-4-20250514`)
- [x] Delivers via Discord/Slack webhook (documented)
- [x] Configurable variables: GitHub repo, destination channel, language (EN/FR)
- [ ] Tested on a real n8n instance (screenshot needed)
- [x] README with setup instructions in 5 steps or fewer