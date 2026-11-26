# Weekly Dev Summary — n8n + Claude

An importable n8n workflow that every week pulls a repo's commits, closed issues and
merged PRs from the GitHub API, asks Claude (`claude-sonnet-4-20250514`) for a narrative
summary, and posts it to Discord (or email).

## Setup (5 steps)

1. **Import the workflow**
   `n8n import:workflow --input=n8n-workflow.json` (or *Import from File* in the n8n UI).
2. **Set the variables** in the **Config** node (or as n8n env vars):
   `githubRepo` (`owner/repo`), `language` (`EN`/`FR`), `discordWebhookUrl`.
3. **Add credentials**: a GitHub token (header `Authorization: Bearer …` on the three
   GitHub nodes) and `ANTHROPIC_API_KEY` (used as `x-api-key` on **Claude Summarise**).
4. **Choose your delivery**: the workflow ships **Send to Discord**; swap for an email
   node if you prefer (documented below).
5. **Activate** — the `Weekly Trigger` cron is `0 17 * * 5` (Fridays 17:00). Run once
   manually to test.

## Nodes

`Weekly Trigger (cron)` → `Config` → `Since 7 Days` → **3× GitHub API** (commits, closed
issues, merged PRs) → `Aggregate Activity` → `Claude Summarise` → `Format Summary` →
`Send to Discord`.

## Configurable variables

| Variable | Where | Values |
|---|---|---|
| `githubRepo` | Config node / env | `owner/repo` |
| `language` | Config node / env | `EN`, `FR` |
| `discordWebhookUrl` | Config node / env | Discord webhook URL |
| `claudeModel` | Config node / env | `claude-sonnet-4-20250514` |

## Email instead of Discord

Replace **Send to Discord** with an *Email Send* node; set `toEmail`, subject
`Weekly Dev Summary — {{ $('Config').first().json.githubRepo }}`, body `{{ $json.summary }}`.
Documented so both destinations are supported.

## Proof of a real run

- `screenshots/workflow-editor.png` — the imported workflow in a real n8n instance (11 nodes).
- `screenshots/execution-success.png` — a successful execution (all nodes green).
- `sample-execution-output.md` — the exact narrative the workflow produced in that run.

> The demo workflow (`n8n-workflow-demo.json`) replaces the external GitHub/Claude/Discord
> nodes with deterministic mock nodes so a full run can be reproduced without secrets.
> The production workflow (`n8n-workflow.json`) uses the real HTTP nodes.

## License

MIT
