# Weekly GitHub Dev Summary — n8n workflow (Claude-powered)

An importable n8n workflow that, every Friday at 5pm, pulls a GitHub repo's last
7 days of activity (commits, merged PRs, closed issues) and posts a **narrative
weekly summary** written by Claude, to Discord/Slack **or** email.

## Setup (5 steps)

1. **Import**: n8n → *Workflows* → *Import from File* → select `weekly-github-summary.json`.
2. **GitHub credential**: create a *GitHub API* credential with a read-only PAT
   (`public_repo` / `repo:read`) and attach it to the three `GitHub *` nodes.
3. **Anthropic credential**: create an *Header Auth* credential — name `x-api-key`,
   value your Anthropic API key — and attach it to the `Claude Summary` node.
4. **Configure**: open the `Config` node and set `githubOwner`, `githubRepo`,
   `language` (`EN`/`FR`), `deliveryChannel` (`discord`/`email`), and either
   `discordWebhookUrl` or `emailTo` (+ SMTP credential on `Send Email`).
5. **Activate**: toggle the workflow *Active*. To test now, hit *Execute Workflow*.

## Node flow

```
Weekly Trigger (Fri 5pm)  →  Config  →  Compute Since Date
                                            ├─→ GitHub Commits ┐
                                            ├─→ GitHub PRs     ├─→ Build Digest → Claude Summary → Format Output → If Discord ─┬─→ Send Discord
                                            └─→ GitHub Issues  ┘                                                              └─→ Send Email
```

## Configurable variables (the `Config` node)

| Variable | Default | Notes |
|----------|---------|-------|
| `githubOwner` / `githubRepo` | `n8n-io` / `n8n` | any public/private repo your PAT can read |
| `language` | `EN` | `EN` or `FR` — switches the Claude prompt |
| `deliveryChannel` | `discord` | `discord` or `email` |
| `discordWebhookUrl` | placeholder | Discord/Slack-compatible webhook URL |
| `emailTo` | placeholder | used when `deliveryChannel=email` |
| `claudeModel` | `claude-sonnet-4-20250514` | swap when a newer model ships |

## Verified

- **Structure**: passes n8n's own import rules (`validate_workflow.py` mirrors
  `packages/workflow/src/workflow-structure-validation.ts`) — 12 nodes, 1 trigger,
  no duplicate names/ids, all connection endpoints resolve.
- **JavaScript**: all three Code nodes compile under `node --check`.
- **Expressions**: every `{{ }}` fragment in URLs/body/message compiles.
- **Cron**: `0 17 * * 5` = every Friday 17:00 (5 fields, valid).

> ⚠️ **Not yet run against a live n8n instance**: Docker was unavailable in the
> build environment. Import + one manual *Execute Workflow* run on your instance
> is the remaining step to capture the execution screenshot.

## Files

- `weekly-github-summary.json` — the importable workflow
- `validate_workflow.py` — offline structural validator (no n8n needed)

MIT licensed.
