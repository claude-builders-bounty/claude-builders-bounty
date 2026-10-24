# Weekly Dev Summary (n8n + Claude)

Importable n8n workflow: weekly cron → GitHub API (commits, closed issues, merged PRs, fetched in sequence) → Claude `claude-sonnet-4-20250514` narrative → Slack/Discord webhook.

## Setup (5 steps)

1. **Import:** n8n → Workflows → Import from file → `workflows/weekly-dev-summary.json`.
2. **Set env/vars:** `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DELIVERY_WEBHOOK_URL` (Slack/Discord incoming webhook), `SUMMARY_LANG` (`EN` or `FR`).
3. **Schedule:** the `Weekly Cron` node already uses `0 17 * * 5` (Friday 17:00, instance timezone). Change it there if needed.
4. **Test:** Execute Workflow → confirm `Deliver: webhook` returns 2xx and message appears in channel; save screenshot as `docs/weekly-summary-proof.png`.
5. **Activate:** toggle Active. No secrets are stored in the JSON (all via env/expressions).

## Notes

- The three GitHub calls run one after another and only once each, so the aggregate step always sees all of them.
- Request bodies are built with `JSON.stringify`, so quotes or newlines in commit messages and PR titles don't break the Claude or webhook calls.
- Only the last 7 days are kept; each list is capped at 50 entries to keep the prompt small.
