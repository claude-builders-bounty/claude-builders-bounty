# Weekly Dev Summary — n8n + Claude

An n8n workflow that reads a GitHub repository once a week, asks Claude for a narrative
summary, and posts it to Discord.

```
Friday 17:00 ──► GitHub: commits + merged PRs + closed issues ──► Claude ──► Discord
```

## Setup — 5 steps

1. **Import**: in n8n open *Workflows → ⋯ → Import from file* and pick `weekly-dev-summary.json`.
2. **Configure**: open the **Config** node and set `owner`, `repo`, `language` (`en` or `fr`),
   `anthropicApiKey`, `githubToken` and `discordWebhookUrl`.
3. **Test**: click **Execute workflow** (the Manual Test trigger). The Discord channel
   receives the summary of the last 7 days.
4. **Activate**: toggle the workflow active. The schedule trigger runs `0 17 * * 5`
   (Friday 17:00, server timezone).
5. **Optional hardening**: instead of pasting secrets into the Config node, create
   *Variables* (`GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`) and point the
   fields at them: `{{ $vars.GITHUB_TOKEN }}`. The node's values are plain text, so anyone
   who can export the workflow can read them.

Requirements: n8n 1.60+ (verified on 2.45.7), a GitHub token with `public_repo` for public
repositories or `repo` for private ones, an Anthropic API key, and a Discord webhook URL
(*Channel settings → Integrations → Webhooks → New webhook*).

## Configurable variables

| Variable | Default | Meaning |
|---|---|---|
| `owner` / `repo` | `n8n-io` / `n8n` | repository to summarise |
| `language` | `en` | output language, `en` or `fr` |
| `days` | `7` | reporting window length |
| `model` | `claude-sonnet-4-20250514` | model id sent to the API |
| `anthropicBaseUrl` | `https://api.anthropic.com` | override for a proxy or a test stub |
| `anthropicApiKey` | placeholder | sent as `x-api-key` |
| `githubToken` | placeholder | sent as `Authorization: Bearer` |
| `discordWebhookUrl` | placeholder | destination |

The cron expression lives in the **Every Friday 17:00** node. Any valid 5-field cron works.

## What each node does

| Node | Purpose |
|---|---|
| Every Friday 17:00 | schedule trigger, `0 17 * * 5` |
| Manual Test | run the same flow on demand without changing the schedule |
| Config | every setting in one place, so nothing is buried in an expression |
| Reporting Window | Code node: turns `days` into `since`, `sinceDay`, `untilDay` and `periodLabel`, so every date calculation lives in one place |
| GitHub: Commits | `GET /repos/{owner}/{repo}/commits?since=…` |
| GitHub: Closed Issues | `GET /repos/{owner}/{repo}/issues?state=closed&since=…`, PR entries filtered out |
| GitHub: Merged PRs | `GET /search/issues?q=repo:… is:pr is:merged merged:>=…` |
| Build Digest | merges the three responses into one text digest: counts, commit subjects, PR and issue numbers. Caps at 60 commits / 40 PRs / 40 issues so the prompt stays bounded |
| Claude: Weekly Summary | `POST /v1/messages` with the digest as the single user message |
| Format Message | extracts `content[0].text`, prepends repository/period/counts, truncates to Discord's 2000-character limit |
| Has Activity? | skips delivery when the week has zero commits, PRs and issues |
| Discord: Post Summary | posts `{"content": …}` with `allowed_mentions: {"parse": []}` so a PR title cannot ping `@everyone` |

## Prompt and output

The system prompt asks for one summary paragraph, 3–5 **Highlights** bullets and 1–3
**Worth watching** bullets, in the configured language, citing PR and issue numbers, with
an explicit instruction to invent nothing that is not in the digest. The digest is data,
not instructions, so a hostile issue title cannot redirect the model.

Temperature is 0.3, `max_tokens` 1200. A typical run on a mid-size repository costs about
1.5–3k input tokens and ~300 output tokens.

Example delivery:

```
**Weekly update — n8n-io/n8n** (2026-10-24 → 2026-10-31)
_58 commits · 42 merged PRs · 18 closed issues_

Development this week was dominated by stabilising the execution engine…

**Highlights**
- Execution engine: retries and cancellation were reworked so a stopped workflow no longer
  leaves orphaned child executions (#14281, #14296).
…
```

## Reliability

- Every GitHub and Discord request retries (3 attempts, 2–3 s apart); the Claude call retries
  once after 5 s. GitHub and Discord are idempotent here; a retried Claude call only costs
  tokens.
- HTTP timeouts: 20 s for GitHub, 120 s for Claude, 15 s for Discord.
- `Has Activity?` prevents an empty "nothing happened" post during quiet weeks.
- Failures surface in n8n's execution list with the failing node and the API body; no
  partial message is posted, because Format Message throws before delivery when the model
  returns no text block.

## Testing

Two offline checks ship with the workflow:

```bash
# 1. structure: ids, connections, cron, required config, JS syntax in Code nodes
node test/validate-workflow.mjs

# 2. a successful run without an Anthropic key or a Discord workspace
python3 test/anthropic-stub.py --port 8799
# Config → anthropicBaseUrl = http://127.0.0.1:8799
# Config → discordWebhookUrl = http://127.0.0.1:8799/webhook
# then Execute workflow
```

The stub answers `/v1/messages` with a realistic Anthropic response and accepts any
`POST /webhook` with 204, printing the delivered payload, so the whole chain runs offline.

`test/validate-workflow.mjs` reports **12 nodes, 11 connection groups, 0 problems** on the
shipped file. The screenshot in [`test/n8n-execution.png`](test/n8n-execution.png) is a real
n8n 2.45 execution against the live GitHub API (`n8n-io/n8n`, 100 commits / 100 merged PRs /
4 closed issues in the window); the Claude call in that run was answered by the stub and the
Discord call went to the stub's `/webhook` sink, because the test environment had no
Anthropic key and no Discord workspace. Everything else — auth headers, query building,
digest assembly, response parsing, `Has Activity?`, delivery payload — ran for real. The
stub printed the payload it received:

```
DELIVERED {"content": "**Weekly update - n8n-io/n8n** (2026-10-24 to 2026-10-31)\n
_100 commits · 100 merged PRs · 4 closed issues_\n\nDevelopment this week was dominated by…"}
```

### What the local run caught

Three real bugs were found only by executing the workflow, and are fixed in this version:

1. **Set-node cross-reference (HTTP 422).** `Reporting Window` originally computed `sinceDay`
   as `{{ $json.since.slice(0, 10) }}`. Set-node assignments are evaluated against the node's
   *input*, not against the other assignments, so `sinceDay` came out empty, the search query
   became `merged:>=` and GitHub answered `422 Validation Failed`. The window is now a Code
   node that builds all fields from one `Date` pair.
2. **Reference to a skipped node.** A node that produces zero items is not executed, so
   `$('GitHub: Closed Issues').all()` threw and the whole run failed on quiet repositories.
   `Build Digest` now wraps each lookup in `try/catch` and falls back to an empty list.
3. **Stub crash on a non-UTF-8 console.** Printing the delivered payload raised
   `UnicodeEncodeError` on a cp1251 console, killing the handler before the 204, which the
   client reported as `socket hang up`. The stub now escapes unprintable characters, speaks
   HTTP/1.1 and sends an explicit `Content-Length: 0` with the 204.

## Notes and limits

- GitHub's `since` filter on issues is based on `updated_at`, so an issue closed this week
  but touched earlier can be missed; the search API for merged PRs is exact.
- Repositories with more than 100 commits or PRs in a week are summarised from the first
  100 returned by the API; the digest states the counts it actually saw.
- Discord caps a message at 2000 characters, so long summaries are truncated with a marker.
  For longer reports, swap the Discord node for the Slack or Email node — the message field
  is the only thing that needs to change.
- The workflow stores no state; each run is independent and can be re-run safely.
