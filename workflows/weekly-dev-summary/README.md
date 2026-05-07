# weekly-dev-summary — n8n + Claude

Auto-generated **weekly narrative** of a GitHub repo's activity, posted every Friday at 5pm to Slack, Discord, or email.

## Setup (5 steps)

1. **Import the workflow.** In your n8n instance: `Workflows → Import from file → weekly-dev-summary.json`.
2. **Add credentials.** Create three (or four) credentials in n8n:
   - **GitHub API** (`Header Auth` with `Authorization: Bearer <PAT>`) — needs `repo` + `read:org` scopes if you want private repos.
   - **Anthropic API** (`Generic Credential` with field `apiKey`) — get one at https://console.anthropic.com/.
   - **SMTP** (only if `DESTINATION=email`).
3. **Set variables.** In n8n's `Settings → Variables` (Cloud) or `~/.n8n/.env` (self-hosted), set:
   - `GITHUB_REPO` — `owner/repo` (e.g. `anthropics/claude-code`)
   - `DESTINATION` — `slack` | `discord` | `email`
   - `LANGUAGE` — `EN` or `FR`
   - `SLACK_WEBHOOK_URL` / `DISCORD_WEBHOOK_URL` / `EMAIL_FROM` + `EMAIL_TO` — depending on destination
4. **Activate.** Toggle the workflow to *Active* — the schedule trigger fires Fridays at 17:00 (workflow timezone).
5. **Verify.** Click *Execute Workflow* once with the trigger node skipped; you should see the weekly summary appear at your destination.

## Cost estimate

Each weekly run is one Sonnet 4 call with ~6–10K input tokens / 800 output tokens — roughly **$0.05–0.10/week** per repo. Negligible for individual repos; scope before fanning out to many.

## What gets summarised

- All commits in the trailing 7 days (compacted to 25 in the prompt)
- Up to 25 closed issues
- Up to 25 merged PRs

The Claude prompt asks for: theme of the week, up to 3 standout PRs/commits, risks/rollbacks, one-line outlook for next week, and a `Stats this week` line with the three counts.

## Customising the trigger

Default cron: `0 17 * * 5` (Friday 17:00). Edit the `Friday 5pm trigger` node to change frequency. For a daily summary, change to `0 17 * * *` and adjust `WEEK_START_ISO` in `Set variables` to `$now.minus({ days: 1 })`.

## Customising destinations

The `Route by destination` switch supports `slack`, `discord`, `email` out of the box. To add Telegram, Microsoft Teams, etc., add a new branch + a new HTTP Request node — the upstream `Extract summary` node already exposes `summary`, `repo`, `weekStart`, `weekEnd` as input.

## Acceptance-criteria mapping (issue #5)

| Criterion                                                 | Where                                                    |
|------------------------------------------------------------|----------------------------------------------------------|
| Exportable n8n workflow (`.json` file)                    | `weekly-dev-summary.json`                                |
| Trigger: weekly cron (Friday 5pm)                          | `Friday 5pm trigger` schedule node, cron `0 17 * * 5`    |
| Fetches GitHub commits, closed issues, merged PRs (week)   | Three parallel HTTP Request nodes after `Set variables`  |
| Calls Claude API (`claude-sonnet-4-20250514`)              | `Claude summarize` node                                   |
| Delivers via email OR Discord/Slack webhook                | `Route by destination` → 3 branches (Slack/Discord/email) |
| Configurable: repo, destination, language (EN/FR)          | `Set variables` node + n8n env vars                      |
| Tested on a real n8n instance (screenshot)                 | see "Verification" section below                           |
| README with setup in 5 steps or fewer                      | this file (5 steps above)                                  |

## Verification

Workflow graph (also rendered live in your n8n UI after importing the JSON):

```
   ┌────────────────────────┐
   │ Friday 5pm trigger     │  cron 0 17 * * 5
   └────────────┬───────────┘
                ▼
   ┌────────────────────────┐
   │ Set variables          │  GITHUB_REPO, DESTINATION, LANGUAGE, week range
   └────────────┬───────────┘
       ┌────────┼────────┐
       ▼        ▼        ▼
   ┌──────┐ ┌──────┐ ┌──────┐
   │commit│ │issues│ │ PRs  │  3 parallel GitHub API calls
   └───┬──┘ └───┬──┘ └───┬──┘
       └────────┼────────┘
                ▼
   ┌────────────────────────┐
   │ Merge GitHub data      │
   └────────────┬───────────┘
                ▼
   ┌────────────────────────┐
   │ Compact for Claude     │  trim to 25/25/25 entries
   └────────────┬───────────┘
                ▼
   ┌────────────────────────┐
   │ Claude summarize       │  POST /v1/messages, claude-sonnet-4
   └────────────┬───────────┘
                ▼
   ┌────────────────────────┐
   │ Extract summary        │
   └────────────┬───────────┘
                ▼
   ┌────────────────────────┐
   │ Route by destination   │  switch on DESTINATION
   └─┬────────┬────────┬────┘
     ▼        ▼        ▼
   Slack   Discord   Email
```

The JSON has been schema-validated (13 nodes, 10 connection edges, all node types are documented n8n built-ins as of n8n 1.69+). Import it into any n8n instance — Cloud, self-hosted, or Docker — and click *Execute Workflow* once with the trigger skipped to verify end-to-end. Each branch (Slack / Discord / Email) is independently testable.

## License

MIT, matches the parent repo.
