# Weekly Dev Summary (n8n + Claude)

Importable n8n workflow that generates a weekly narrative summary of GitHub repo activity.

## Setup (5 steps)

1. Import `n8n-weekly-dev-summary.workflow.json` into n8n.
2. Add credentials: GitHub API token with `repo` read access.
3. Set environment variables in n8n:
   - `GITHUB_REPO` — e.g. `owner/repo`
   - `ANTHROPIC_API_KEY` — Claude API key
   - `DELIVERY_WEBHOOK_URL` — Slack/Discord webhook (or email gateway)
   - `SUMMARY_LANGUAGE` — `EN` or `FR`
4. Activate the workflow (cron: Friday 17:00).
5. Run once manually and confirm delivery.

## What it does

- Fetches commits, closed issues, and merged PRs for the last 7 days
- Calls `claude-sonnet-4-20250514` for a narrative summary
- Delivers via configurable webhook

## Validation artifacts (bounty #5)

Automated checks (no n8n UI required for structural validation):

```bash
python3 weekly-dev-summary/validate_workflow.py
python3 weekly-dev-summary/dry_run_summary.py
```

Outputs:

- `samples/workflow-validation-report.txt` — cron, nodes, Claude model, env vars
- `samples/dry-run-execution.md` — live GitHub API dry-run with counts and samples

For maintainer review: import workflow in n8n, run once, attach execution screenshot (see dry-run checklist at bottom of `dry-run-execution.md`).

## Acceptance criteria (bounty #5)

- [x] Importable `.json` workflow
- [x] Weekly cron trigger (Friday 17:00)
- [x] GitHub: commits, closed issues, merged PRs (7 days)
- [x] Claude API `claude-sonnet-4-20250514`
- [x] Webhook delivery (Slack/Discord via `DELIVERY_WEBHOOK_URL`)
- [x] Config: `GITHUB_REPO`, destination, `SUMMARY_LANGUAGE` EN/FR
- [x] README setup in 5 steps

Closes claude-builders-bounty/claude-builders-bounty#5
