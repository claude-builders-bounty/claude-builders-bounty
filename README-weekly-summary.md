# Weekly Dev Summary — n8n + Claude Code

Automatically generates a weekly narrative summary of a GitHub repo (commits, closed
issues, merged PRs) using the Claude API, delivered to Slack every Friday at 17:00.

## Setup (3 steps)

1. **Set env vars on the n8n host**
   ```ini
   GH_REPO=owner/repo          # repo to watch
   GH_TOKEN=github_pat_...     # optional, raises API rate limit
   ANTHROPIC_API_KEY=sk-ant-... # Claude API key
   CLAUDE_MODEL=claude-sonnet-4-20250514
   LANGUAGE=EN                 # EN or FR
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
   TIMEZONE=UTC
   ```
2. **Import the workflow**: n8n → *Workflows* → `Import from file` → `workflow.json`
   (click *3 dots* on the workflow → *Import from File*).
3. **Save + Activate**: run an execution manually once to verify, then toggle **Active**.

## How it works

```
Schedule (Fri 17:00)
   └→ Init context (env: repo, since=now-7d, language)
        ├→ GitHub commits since date  ─┐
        │                              ├→ Merge → Build Claude payload
        └→ GitHub closed issues + PRs ─┘     → Claude API (claude-sonnet-4-20250514)
                                              → Extract summary → Slack webhook
```

## Configurables

- **Repo / language / timezone**: env vars (see above) — change without editing nodes.
- **Deliver channel**: default Slack incoming webhook; to use email instead, replace the
  last HTTP node with n8n's `Email` node (SMTP creds required).
- **Schedule**: change the Schedule Trigger node (e.g. Monday 09:00).

## Verification without n8n

Run the included harness to prove the data pipeline against a live repo
(GitHub step requires no key):

```bash
python dry-run.py --repo expressjs/express --since 2026-01-01 --no-claude
```

If `ANTHROPIC_API_KEY` is exported it also calls the real Claude API and prints the
generated summary.

## Files

- `workflow.json` — importable n8n workflow
- `dry-run.py` — standalone harness (stdlib only) for the same pipeline