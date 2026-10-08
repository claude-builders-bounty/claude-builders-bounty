# Weekly Dev Summary — n8n + Claude (Opire bounty $200, issue #5)

Automated weekly narrative of a GitHub repo's activity: every Friday at 17:00
the workflow pulls the week's commits, closed issues and merged PRs from the
GitHub API, asks Claude for a narrative summary (English or French), and posts
it to Slack.

## Setup — 5 steps

1. In n8n: **Workflows → Import from file** → choose `n8n-weekly-dev-summary.json`.
2. Open the **Config** node and fill in: `repo_owner`, `repo_name`,
   `language` (`EN` or `FR`), `anthropic_api_key`, `slack_webhook_url`.
   `github_token` is optional (only needed for private repos or higher rate
   limits). The bounty spec named `claude-sonnet-4-20250514`, which Anthropic
   retired in June 2026 — the default is the current `claude-sonnet-4-6`
   (change `anthropic_model` if you prefer another current model).
3. Toggle the workflow **Active** — the Friday 17:00 schedule is already set.
4. Optional: select the **Friday 5pm** node and press **Execute workflow** to
   test immediately instead of waiting for Friday.
5. Check Slack for the posted summary.

## What it does

- **Friday 5pm** — schedule trigger, cron `0 17 * * 5`.
- **Config** — all settings in one place: repo, language, model, keys, webhook.
- **Collect GitHub activity** — paginates the GitHub REST API (follows
  `Link: rel="next"`, up to 50 pages), keeps the trailing 7-day window,
  dedupes commits by SHA, excludes PRs from the closed-issues list, and takes
  merged PRs from the pulls endpoint filtered on `merged_at`.
- **Build prompt** — assembles the Claude prompt in English or French from the
  collected data. Quiet weeks produce a one-sentence quiet-week note, never an
  empty post.
- **Ask Claude** — `POST https://api.anthropic.com/v1/messages`, model and key
  from Config.
- **Deliver to Slack** — posts the summary text to your incoming webhook URL.

## Files

- `n8n-weekly-dev-summary.json` — the importable workflow (8 nodes).
- `collect.js`, `prompt.js` — the two Code-node sources (also embedded in the
  JSON by `build_workflow.py`).
- `build_workflow.py` — assembles and mechanically validates the workflow JSON.
- `mirror_test.py` — Python mirror of the collection + prompt logic, run
  against the live GitHub API (see `validation-evidence.md`).
- `evidence/` — real outputs from the validation runs.
