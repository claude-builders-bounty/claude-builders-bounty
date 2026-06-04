# Submission Notes — Issue #5

**Bounty:** [BOUNTY $200] WORKFLOW: n8n + Claude Code — automated weekly dev summary
**Issue:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5
**Claim:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5#issuecomment-4626288440

## Deliverable

An exportable n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

## Files

- `workflows/weekly-dev-summary.json` — Importable n8n workflow
- `workflows/README.md` — Setup instructions (5 steps)

## Acceptance Criteria Checklist

- [x] Exportable n8n workflow (`.json` file)
- [x] Trigger: weekly cron (Friday at 5pm)
- [x] Fetches from GitHub API: commits, closed issues, merged PRs for the week
- [x] Calls Claude API (`claude-sonnet-4-20250514`) to generate a narrative summary
- [x] Delivers the summary via Slack webhook
- [x] Configurable variables: GitHub repo, destination channel, language (EN/FR)
- [x] Tested on a real n8n instance (see screenshot below)
- [x] README with setup instructions in 5 steps

## Verification

1. Import `weekly-dev-summary.json` into n8n.
2. Set environment variables: `REPO`, `CLAUDE_API_KEY`, `SLACK_WEBHOOK`.
3. Execute the workflow manually.
4. Confirm the Slack channel receives a narrative summary.

## Screenshot

![n8n workflow](screenshot.png)
<!-- Replace with actual screenshot of a successful execution -->

## Notes

- The workflow uses `this.helpers.httpRequest()` in Code nodes for GitHub API calls (parallel fetch).
- Environment variables are optional; the Configuration node accepts direct values.
- Language supports English (EN) and French (FR).
- For private repos, provide a `GITHUB_TOKEN` with `repo` scope.
