# Weekly GitHub Dev Summary — n8n + Claude

Delivery for: [BOUNTY $200] WORKFLOW: n8n + Claude Code — automated weekly dev summary

## Setup (5 steps)
1. Import `weekly-summary.workflow.json` into n8n (Workflows → Import from File).
2. Add Header Auth credential for GitHub API (`Authorization: Bearer <YOUR_TOKEN>`).
3. Set env vars: `GITHUB_REPO`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, optional `SUMMARY_LANG` (EN/FR).
4. Attach the GitHub credential to the three GitHub HTTP Request nodes.
5. Execute once manually, confirm Discord delivery, then activate the Friday 17:00 cron.

## Acceptance criteria (truthful status)
- [x] Exportable n8n workflow (importable `.json` file)
- [x] Trigger: weekly cron (Friday 17:00)
- [x] Fetches from GitHub API: commits, closed issues, merged PRs for the week
- [x] Calls Claude API (`claude-sonnet-4-20250514`) to generate a narrative summary
- [x] Delivers the summary via Discord webhook (documented)
- [x] Configurable variables: GitHub repo, destination channel, language (EN/FR)
- [ ] Tested on a real n8n instance (include a screenshot of successful execution) — **UNVERIFIED** (no live n8n execution evidence in this PR yet)
- [x] README with setup instructions in 5 steps or fewer

## Test evidence
Status: **UNVERIFIED** — a real n8n instance execution screenshot is not included.
Do not treat this PR as acceptance-complete until a screenshot of a successful run is attached.

Updated: 2026-09-28T04:26:28Z
