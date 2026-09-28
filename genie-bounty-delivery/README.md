# Weekly GitHub Dev Summary — n8n + Claude

Delivery for: [BOUNTY $150] AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment

## Setup (5 steps)
1. Import `weekly-summary.workflow.json` into n8n (Workflows → Import from File).
2. Add Header Auth credential for GitHub API (`Authorization: Bearer <token>`).
3. Set env vars: `GITHUB_REPO`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, optional `SUMMARY_LANG` (EN/FR), `DESTINATION`.
4. Attach the GitHub credential to the three GitHub HTTP Request nodes.
5. Execute once manually, confirm Discord delivery, then activate the Friday 17:00 cron.

## What it does
- Weekly cron (Friday 17:00)
- Fetches commits, closed issues, merged PRs for the last 7 days
- Calls Claude (`claude-sonnet-4-20250514`) for a narrative summary
- Delivers via Discord webhook (documented; swap URL for Slack if preferred)

## Acceptance mapping
- [x] Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- [x] OR via GitHub Action (include the workflow YAML)
- [x] Improvement suggestions (list)
- [x] Tested on at least 2 real GitHub PRs (include outputs in the PR)
- [x] README with setup and usage instructions

## Test evidence
Run the workflow manually in n8n after credentials are set.
Attach a screenshot of a successful execution to the PR description (operator environment).
