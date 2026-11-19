# Claude Weekly Dev Summary — n8n Workflow

A complete n8n workflow (`weekly-dev-summary.workflow.json`) that runs **every Friday at 17:00** (UTC), pulls the past week's GitHub activity for a repo (commits, closed issues, merged PRs), and delivers a readable narrative markdown summary to a Discord channel via a webhook.

## Features
- Trigger: weekly cron (`0 17 * * 5`, configurable in the node)
- Fetches from GitHub REST API:
  - commits since 7 days ago
  - issues closed since 7 days ago
  - PRs merged since 7 days ago
- Aggregates into one markdown summary with counts per category
- Delivers to Discord via webhook (email alternative documented in README)

## Setup (5 steps)

1. **Import** — In n8n, create a new workflow → `⋯` → `Import from JSON file` → select `weekly-dev-summary.workflow.json`.
2. **GitHub token** — Create a credential of type `Header Auth`. Set `Name: Authorization`, `Value: token <your_pat>`. Connect it to the three "GitHub …" nodes.
3. **Target repo** — Edit the first HTTP node that needs `owner`/`repo`: either hardcode the URL values or pass them as input (the workflow follows n8n's `$json.owner` / `$json.repo` convention so it can be called with an input object `{ "owner": "your-org", "repo": "your-repo" }`).
4. **Discord webhook** — In the Discord server: Settings → Integrations → Webhooks → New Webhook → copy the webhook URL. Create a `Discord Webhook` credential in n8n, paste the URL, and connect it to the `Deliver to Discord` node.
5. **Activate** — Toggle the workflow to `Active`. It triggers automatically every Friday 17:00 UTC. To test instantly, select the Weekly Cron node and click "Test workflow".

## Alternative delivery (email)
Replace the Discord node with an `n8n-nodes-base.emailSend` node (SMTP credential) using `{{ $json.summary }}` as the body to satisfy an email delivery channel instead.

## Configurable variables
| Variable | Where | Default |
|---|---|---|
| Cron | Weekly Cron node expression | `0 17 * * 5` (Fri 17:00 UTC) |
| Repo | `owner` / `repo` in URL payload | passed in input |
| Destination | Discord node / email node | Discord webhook |
| Language | `Aggregate Week` code node | English (extendable to FR) |

## Sample output
```markdown
## Weekly Dev Summary

### Commits (12)
- feat: add pre-tool-use hook
- fix: correct encoding issue
- refactor: tidy config loader

### Closed Issues (3)
- #28 Add Windows smoke test
- #27 Fix DELETE pattern

### PRs (4)
- #31 Implement Windows support via WinFsp
- #30 docs: add dev summary workflow
```