# n8n weekly dev summary workflow

Exportable n8n workflow for issue #5: weekly cron → GitHub activity → Claude narrative → Slack webhook.

## Setup (5 steps)

1. **Import** `weekly-dev-summary.workflow.json` in n8n (Workflows → Import from File).
2. **Credentials** — create two HTTP Header Auth credentials:
   - `GitHub Token Header`: header `Authorization`, value `token <GITHUB_TOKEN>`
   - `Anthropic API Key Header`: header `x-api-key`, value your Anthropic key
3. **Environment** — set `SLACK_WEBHOOK_URL` on the n8n instance (Incoming Webhook URL).
4. **Configure** — open the **Config** node and set `github_repo` (default `owner/repo`) and `language` (`EN` or `FR`).
5. **Activate** — map credentials on the three HTTP nodes, click **Test workflow**, then toggle **Active** (Friday 17:00 UTC cron).

Delivery is via **Slack webhook** (documented here). Swap the last node for Discord if you prefer the same JSON `{"text": "..."}` POST.

## Nodes

| Node | Role |
|------|------|
| Friday 5pm UTC | Schedule trigger, cron `0 17 * * 5` |
| Config | `github_repo`, `language`, webhook URL |
| Week Window | Computes 7-day `since` timestamp |
| GitHub ×3 | Commits, closed issues, merged PRs |
| Build Prompt | Aggregates activity into Claude prompt |
| Claude Summary | `claude-sonnet-4-20250514` via Messages API |
| Slack Webhook | Posts narrative to channel |

## Local dry-run (no n8n)

```bash
python3 dry_run.py --repo claude-builders-bounty/claude-builders-bounty
```

Requires `GITHUB_TOKEN` and optionally `ANTHROPIC_API_KEY` in the environment.
