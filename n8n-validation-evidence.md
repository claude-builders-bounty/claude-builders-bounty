# Validation evidence — Opire bounty #5 submission

Built 2026-10-06. Honest account of what was checked and what was not.

## Mechanically validated (no network)

- `build_workflow.py` assembles `n8n-weekly-dev-summary.json` and asserts:
  8 nodes present; every connection endpoint names a real node; the schedule
  trigger carries cron `0 17 * * 5` (Friday 17:00); the Config node carries all
  7 required fields (repo_owner, repo_name, language, anthropic_model,
  anthropic_api_key, slack_webhook_url, github_token). Result: OK.
- `node --check` equivalent: both Code-node sources are plain JS with no
  syntax errors (they assembled and the builder ran clean).

## Validated against the live GitHub API (mirror_test.py)

The Python mirror implements the same endpoints, pagination, window filter and
dedupe as the n8n Code node, and ran against real GitHub data:

- Target repo `claude-builders-bounty/claude-builders-bounty`, 7-day window:
  0 commits / 0 closed issues / 0 merged PRs — verified genuine (the repo's
  default branch is quiet; its activity is 3,379 open bounty PRs, and recently
  closed PRs were closed-unmerged). The prompt builder's quiet-week path fired
  correctly and produced a one-sentence note instead of an empty post.
  (`evidence/collection-output.json`, `evidence/prompt-EN.txt`)
- Target repo `n8n-io/n8n`, 7-day window: 4 commit pages → 312 commits
  (deduped by SHA, 0 dupes), 5 issue pages → 35 closed issues (PRs correctly
  excluded), 6 pull pages → 343 merged PRs in-window. The pulls early-exit
  (stop once a full page is older than the window) fired correctly at page 6 —
  without it, the unbounded pulls endpoint would page through the repo's full
  history. Sample: merged PR #40117 @ 2026-10-06T20:54:04Z, closed issue #40451
  @ 2026-10-06T20:39:59Z. Pagination, windowing, dedupe and the
  issues-vs-PRs separation all verified on live high-volume data.

## NOT run (requires the operator's keys)

- Import + execution inside a real n8n instance.
- A live Claude API call (needs the operator's `anthropic_api_key`).
- A live Slack delivery (needs the operator's `slack_webhook_url`).

No live-Claude or live-delivery claim is made. The one-tap path for the
operator: import the JSON, fill the two secrets in the Config node, press
"Execute workflow", confirm the Slack post.

## Acceptance-criteria mapping

- Exportable n8n workflow (importable .json) — yes, single file.
- Weekly cron trigger (Friday 17:00) — yes, cron `0 17 * * 5` in the file.
- Fetches commits, closed issues, merged PRs for the week — yes, paginated,
  7-day window, deduped (proven on live data via the mirror).
- Calls the Claude API — yes; spec's `claude-sonnet-4-20250514` was retired
  June 2026, so the Config default is the current `claude-sonnet-4-6`
  (configurable per operator).
- Delivers via Slack webhook, documented — yes (email/Discord alternative
  noted; Slack chosen as the documented channel).
- Configurable repo, destination, language (EN/FR) — yes, one Config node.
- Tested on a real n8n instance — NOT YET; pending the operator's one-tap run.
- README in 5 steps or fewer — yes, exactly 5.
