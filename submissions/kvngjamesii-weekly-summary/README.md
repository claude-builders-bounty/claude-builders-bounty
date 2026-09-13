# n8n + Claude — automated weekly GitHub dev summary

**Bounty:** [#5 — $200](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)  
**Author:** KvngJamesII

Importable n8n workflow that every Friday 17:00:

1. Reads configurable `GITHUB_OWNER` / `GITHUB_REPO` / `SUMMARY_LANG` (EN|FR)
2. Fetches commits, closed issues, and merged PRs for the last 7 days
3. Calls Claude (`claude-sonnet-4-20250514`) for a narrative summary
4. Delivers via **Discord webhook** (swap URL for Slack incoming webhook if preferred)

## Setup (≤5 steps)

1. Import `weekly-github-summary.workflow.json` into n8n (**Workflows → Import**)
2. Create Header Auth credential: name `Authorization`, value `Bearer <GITHUB_PAT>`
3. Set env vars: `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, optional `GITHUB_OWNER`, `GITHUB_REPO`, `SUMMARY_LANG`
4. Attach the GitHub credential to the three GitHub HTTP nodes
5. Execute once (or wait for Friday cron) and confirm Discord message

## Files

| File | Purpose |
|------|---------|
| `weekly-github-summary.workflow.json` | Importable n8n workflow |
| `sample-output.md` | Example narrative payload |
| `dry_run_fetch.py` | Proves GitHub fetch path without n8n UI |
| `assets/dry-run-fetch.json` | Captured live API stats from a real repo |

## Screenshot / execution proof

Run locally:

```bash
export GITHUB_TOKEN=$(gh auth token)
python3 dry_run_fetch.py   # writes assets/dry-run-fetch.json
```

Full Claude+Discord path requires n8n + keys; the workflow JSON is complete and import-ready. If a UI screenshot is required for merge, attach after one Execute Workflow run in your n8n instance.

## Distinctives

- Parallel GitHub fetches → single aggregate Code node (no racey Set hacks)
- EN/FR language switch via env
- Model pinned to bounty-required `claude-sonnet-4-20250514`
- Discord delivery with 1900-char safety trim
