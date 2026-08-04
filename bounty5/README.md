# Bounty #5 — n8n weekly GitHub → Claude narrative ($200 Opire)

Importable n8n workflow that every Friday 17:00 builds a weekly dev summary.

## Setup (≤5 steps)

1. Import `bounty5/weekly-dev-summary.workflow.json` into n8n (**Workflows → Import**).
2. Create credentials: **GitHub** (PAT with `repo` or public_repo) + **Header Auth** named `Anthropic API` with header `x-api-key` = your Anthropic key.
3. Set workflow variables (n8n **Variables** or edit Set node defaults):
   - `GITHUB_OWNER`, `GITHUB_REPO`
   - `SUMMARY_LANG` = `EN` or `FR`
   - `DISCORD_WEBHOOK_URL` **or** leave empty and set `EMAIL_TO` + SMTP credential on the Email node
4. Activate workflow (cron: `0 17 * * 5` server timezone).
5. Run **Test workflow** once → check Discord/email body.

## What it does

| Step | Node | Behavior |
|------|------|----------|
| 1 | Schedule | Weekly Friday 17:00 |
| 2 | Set config | Owner/repo/lang/destinations from vars |
| 3–5 | GitHub HTTP | Commits, closed issues, merged PRs since 7 days ago |
| 6 | Code | Merge + truncate payload for Claude |
| 7 | Claude HTTP | `POST https://api.anthropic.com/v1/messages` model `claude-sonnet-4-20250514` |
| 8 | IF | Discord webhook configured? |
| 9a/9b | Discord or Email | Deliver narrative |

## Acceptance map

- [x] Exportable `.json` workflow
- [x] Weekly cron trigger
- [x] GitHub commits + closed issues + merged PRs
- [x] Claude API narrative (`claude-sonnet-4-20250514`)
- [x] Discord webhook **or** email delivery
- [x] Configurable repo, destination, EN/FR
- [x] README ≤5 steps
- [ ] Screenshot on a live n8n instance — run step 5 and attach to PR if reviewer requires

## Test without full n8n UI

```bash
python3 bounty5/tests/test_workflow_json.py
```

## Bounty

https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5
