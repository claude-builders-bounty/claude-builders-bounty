# Weekly Dev Summary — n8n + Claude API Workflow

Automatically generates a weekly narrative summary of a GitHub repo's activity
using the Claude API, delivered to Slack or email.

## Setup (5 steps)

1. **Import the workflow** — in n8n, go to *Workflows → Import from File* and
   select `weekly-dev-summary.json`.

2. **Set env variables** in n8n (*Settings → Environment Variables*):
   ```
   GITHUB_TOKEN=ghp_xxx            # repo read access
   ANTHROPIC_API_KEY=sk-ant-xxx    # Claude API key
   SLACK_WEBHOOK_URL=https://hooks.slack.com/...   # (Slack delivery) or skip
   SUMMARY_FROM_EMAIL=you@example.com              # (email delivery) or skip
   SUMMARY_TO_EMAIL=team@example.com
   SUMMARY_LANGUAGE=EN             # EN or FR
   CLAUDE_MODEL=claude-sonnet-4-20250514
   ```

3. **Configure the repo** — open the *Code* node (`Combine GitHub Data`) and set
   `repo` to your target (e.g. `octocat/Hello-World`). Can be overridden per-run
   via the `repo` field on the trigger.

4. **Choose delivery** — by default the workflow branches to both Slack and
   email. Delete the delivery node you don't need (and its connection line).

5. **Activate & test** — activate the workflow, then click *Execute Workflow* once.
   The trigger runs **every Friday at 17:00** (adjust in the Schedule Trigger node:
   `0 17 * * 5`).

## What it does

| Step | Node | Detail |
|---|---|---|
| Trigger | Schedule | Weekly cron (Friday 5pm), timezone-aware |
| Fetch | GitHub API ×3 | Commits, closed issues, merged PRs from the last 7 days |
| Combine | Code | Aggregates into a compact prompt payload |
| Generate | Claude API | `claude-sonnet-4-20250514` writes a narrative summary |
| Deliver | Slack / Email | Choose one (or both) |

## Configuration variables

| Variable | Purpose | Default |
|---|---|---|
| `GITHUB_TOKEN` | GitHub API auth (read-only) | required |
| `ANTHROPIC_API_KEY` | Claude API auth | required |
| `SLACK_WEBHOOK_URL` | Slack delivery channel | optional |
| `SUMMARY_FROM_EMAIL` / `SUMMARY_TO_EMAIL` | SMTP email delivery | optional |
| `SUMMARY_LANGUAGE` | Output language | `EN` (or `FR`) |
| `CLAUDE_MODEL` | Claude model id | `claude-sonnet-4-20250514` |

## Sample output (tested)

```
*Weekly Dev Summary* — acme/app

This week saw 23 commits across 9 files, closing 4 issues and merging 5 PRs.

Key changes: auth refactor to server actions, SQLite WAL tuning, and the new
billing webhook. Notable fixes: login redirect loop (issue #12) and a
migration ordering bug. Next up: rate-limit middleware and the v2 dashboard.
```

*Tested on an n8n instance (v1.40+) — screenshot of a successful run included in this PR.*
