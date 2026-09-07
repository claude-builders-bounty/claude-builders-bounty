# n8n Weekly Dev Summary (GitHub + Claude + Discord)

Automated weekly dev summary for the **$200 bounty** ([issue #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)): cron → GitHub API (commits, closed issues, merged PRs) → Claude `claude-sonnet-4-20250514` → Discord webhook (email alternative documented).

## Setup — 5 steps

1. **Import:** n8n → Workflows → Import from file → select `workflow.json` → confirm all 14 nodes appear (see `assets/SCREENSHOT_GUIDE.md` for the 2-minute screenshot).
2. **Configure:** open `Config (Edit Me)` → set `owner`, `repo`, `language` (`EN`/`FR`), `discord_webhook_url` (`YOUR_DISCORD_WEBHOOK_URL` → real webhook: Discord channel → Edit channel → Integrations → Webhooks → New).
3. **Add Claude key:** n8n env `ANTHROPIC_API_KEY` (Docker: `-e ANTHROPIC_API_KEY=sk-ant-...`, self-hosted: export before `n8n start`). No keys are stored in the workflow.
4. **Test:** Execute Workflow → check `Discord Notify` output; run `python test_workflow.py` locally (validates JSON + node logic + mocked EN/FR prompts).
5. **Activate:** toggle Active. Cron `0 17 * * 5` = Friday 5pm. Samples: `samples/summary_EN.md`, `samples/summary_FR.md`.

## Config vars

| Var | Where | Default |
|---|---|---|
| `owner` / `repo` | `Config (Edit Me)` | `claude-builders-bounty` / `claude-builders-bounty` |
| `language` | `Config (Edit Me)` | `EN` (`FR` supported) |
| `discord_webhook_url` | `Config (Edit Me)` | `YOUR_DISCORD_WEBHOOK_URL` |
| `ANTHROPIC_API_KEY` | n8n env (`$env.ANTHROPIC_API_KEY`) | placeholder, never committed |
| `max_items_per_source` | `Config (Edit Me)` | `30` |

## How it works

`Weekly Schedule (0 17 * * 5)` → `Config` → `Compute Week Window` (since = now − 7d) → parallel `Fetch Commits` / `Fetch Closed Issues` / `Fetch Merged PRs` (public GitHub API, unauthenticated) → `Filter Merged PRs` (`merged_at != null` + in-window) → `Merge Commits + Issues` → `Merge All Activity` → `Build Claude Prompt (EN/FR)` → `Claude Summary` (`POST https://api.anthropic.com/v1/messages`, model `claude-sonnet-4-20250514`) → `Has Activity?` (IF) → `Discord Notify` (POST webhook, `content` truncated to 1800 chars).

## Email alternative (no extra file)

Duplicate `Discord Notify` → replace with **Send Email** (SMTP) node → Subject `=Weekly dev summary {{ $('Compute Week Window').first().json.since_date }}` → Body `={{ $json.content[0].text }}`. Or add a Slack node (`POST` to Slack webhook URL) with the same body.

## Validation (no live n8n/creds needed)

```bash
python test_workflow.py
```

Checks: valid JSON + n8n export shape, Friday-5pm cron, 3 GitHub HTTP nodes, Claude model + `$env.ANTHROPIC_API_KEY`, Discord webhook placeholder, IF + 2 Merge nodes, no hardcoded secrets, mocked prompt/merge test with sample output.

## License

MIT — see `LICENSE`.
