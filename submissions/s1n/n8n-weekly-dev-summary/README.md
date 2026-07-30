# Weekly GitHub Dev Summary — n8n + Claude

Exportable n8n workflow for Opire/GitHub bounty #5 ($200).

Every **Friday 17:00 UTC** it:
1. pulls last-7-day commits, closed issues, and merged PRs from GitHub
2. asks Claude (`claude-sonnet-4-20250514`) for a short narrative
3. posts the summary to a **Discord webhook**

Configurable: GitHub owner/repo, language (`EN`/`FR`), Discord webhook, delivery label.

## Setup (5 steps)

### 1) Import
In n8n → **Workflows → Import from File** → choose:

`s1n-weekly-github-dev-summary.workflow.json`

### 2) Add credentials
Create two **Header Auth** credentials:

| Credential name suggestion | Header name | Header value |
|---|---|---|
| GitHub PAT | `Authorization` | `Bearer ghp_...` (classic PAT with `repo` or public_repo) |
| Anthropic | `x-api-key` | `sk-ant-...` |

Attach them on:
- **GitHub Commits / Closed Issues / Closed PRs** → GitHub PAT
- **Claude API** → Anthropic

### 3) Edit the **Config** node
Set:

| Field | Example |
|---|---|
| `GITHUB_OWNER` | `n8n-io` |
| `GITHUB_REPO` | `n8n` |
| `LANGUAGE` | `EN` or `FR` |
| `DISCORD_WEBHOOK_URL` | your Discord webhook URL |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` (required by bounty) |
| `MAX_ITEMS` | `40` |

### 4) Manual test
Open workflow → **Execute Workflow** once.

Expect:
- green nodes through Discord
- one Discord message with weekly summary
- take a screenshot of the successful execution (bounty requirement)

### 5) Activate
Toggle workflow **Active**. Cron is already set to `0 17 * * 5` (Friday 17:00 UTC).

## Acceptance checklist

- [x] Exportable importable `.json`
- [x] Weekly cron (Friday 5pm UTC)
- [x] GitHub commits + closed issues + merged PRs (7-day window)
- [x] Claude API model `claude-sonnet-4-20250514`
- [x] Discord webhook delivery (Slack/email: swap final HTTP node; see below)
- [x] Configurable repo + channel + language
- [ ] Screenshot of successful n8n run (do after credentials)
- [x] README ≤ 5 setup steps

## Slack / email variant
Bounty allows email **or** Discord/Slack.

- **Slack:** change final node URL to Slack incoming webhook; body `{"text": "{{content}}"}`.
- **Email:** replace final node with n8n Email/SMTP node; subject `Weekly Dev Summary — {{repo}}`, body = summary text.

## Local dry-run (no Claude spend)
```bash
python3 scripts/dryrun_github.py --owner n8n-io --repo n8n
```
Writes `evidence/dryrun-github-activity.json` and refreshes `docs/sample-output.md`.

## Notes / quality bars vs spam PRs
- Filters pure issues (drops PR-issues from `/issues`)
- Filters merged PRs by `merged_at` inside the 7-day window
- Prompt forbids invented activity
- No secrets baked into JSON
- Named-node aggregation (avoids fragile heterogeneous Merge payloads)

## Requirements
- n8n 1.x+
- GitHub PAT
- Anthropic API key
- Discord webhook
