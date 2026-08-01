# Weekly Dev Summary — n8n + Claude API

> Automated weekly development activity digest powered by Claude (`claude-3-5-sonnet-latest`).
> Every Monday at 9 AM, this workflow pulls the last 7 days of engineering activity from GitHub, Linear/Jira, and Slack, asks Claude to write a structured markdown summary, and publishes it to GitHub Issues, Slack, and/or email.

Built for the Superteam bounty #5: **"$200 — n8n + Claude API: automated weekly dev summary"**.

---

## What it does

1. **Triggers** every Monday at 9 AM (configurable timezone).
2. **Collects** last 7 days of activity from:
   - **GitHub**: PRs opened/merged/closed, issues created/closed (via the Search API).
   - **Linear** (or **Jira** — see Customization): tickets updated/moved/completed. If `LINEAR_API_KEY` is missing, the node runs with `continueOnFail: true` and the prompt explicitly tells Claude to use placeholder data — the workflow still completes.
   - **Slack** `#dev`: last 100 messages in the channel. Same fallback semantics.
3. **Formats** the data into a single prompt with strict sectioning requirements.
4. **Calls** the Anthropic Messages API (`claude-3-5-sonnet-latest`, `max_tokens: 2048`).
5. **Extracts** the markdown text and computes a per-run cost estimate from the response's `usage` block.
6. **Publishes** in parallel to any combination of:
   - **GitHub Issue** in a target repo (default: same repo, with labels `weekly-summary` + `automated`).
   - **Slack** via incoming webhook (with a header + section block + cost footer).
   - **Email** to a distribution list via n8n's built-in SMTP node.

Each publication channel is gated by an `IF` node reading an environment variable (`PUBLISH_GITHUB`, `PUBLISH_SLACK`, `PUBLISH_EMAIL`). Set whichever you want — the rest are no-ops.

---

## Importing the workflow

1. Open your n8n instance (cloud or self-hosted, version 1.x+).
2. In the left sidebar, click **Workflows → ⋯ → Import from File…** (or `Ctrl/Cmd + O` on the workflows page).
3. Select `weekly-dev-summary.json`.
4. The workflow appears in your list, **inactive**. Open it to configure credentials and environment variables (next section).
5. Test by clicking **Execute Workflow** (top right). The first run creates a real GitHub issue / Slack message / email — disable the publish channels you don't want by setting their `PUBLISH_*` env var to `false` first.
6. Once happy, toggle the **Active** switch in the top right.

That's it. No external dependencies beyond the credentials you set in n8n.

---

## Environment variables

Set these in **n8n → Settings → Variables** (cloud) or your `.env` / `docker-compose.yml` (self-hosted). Names match what the workflow references via `$env.*`.

### Required for a useful run

| Variable | What it's for | Where it's used |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API call | `Claude API (claude-3-5-sonnet-latest)` node — `x-api-key` header |
| `GITHUB_TOKEN` | Classic or fine-grained PAT with `repo` (and `issues:write` for fine-grained) scope | `GitHub: PRs last 7d`, `GitHub: Issues last 7d`, `GitHub: Create issue` |
| `GITHUB_OWNER` | GitHub org or user that owns the source repo (e.g. `acme-co`) | URL builder in `Set Date Range` |
| `GITHUB_REPO` | Source repo to read PRs/issues from (e.g. `backend`) | URL builder in `Set Date Range` |

### Optional — for publishing to a different repo

| Variable | Default | Notes |
|---|---|---|
| `GITHUB_TARGET_REPO` | Same as `GITHUB_REPO` | The repo where the weekly summary issue is created. Set if you want summaries in a dedicated repo. |

### Optional — for Linear / Jira integration

| Variable | Notes |
|---|---|
| `LINEAR_API_KEY` | Personal API key from Linear → Settings → API. **If missing, the workflow still runs** — the prompt tells Claude to use placeholder data and the workflow continues. |
| `LINEAR_TEAM_ID` | Optional. Filter the GraphQL query to a specific team. |

To swap Linear for **Jira**, edit the node `Linear: tickets last 7d (mock if no key)` and replace the URL/JSON body with a Jira REST query (e.g. `POST /rest/api/3/search` with a JQL filter on `updated >= -7d`). The downstream prompt is already generic enough to accept any "tickets" JSON.

### Optional — for Slack `#dev` collection

| Variable | Notes |
|---|---|
| `SLACK_BOT_TOKEN` | Bot token (`xoxb-…`) with `channels:history` + `channels:read` scopes. **If missing, the workflow still runs** — the prompt tells Claude to use placeholder data. |
| `SLACK_CHANNEL_ID` | Channel ID (e.g. `C0123456789`) for `#dev`. Find it in Slack: channel → About → scroll down. |

### Optional — for Slack publishing

| Variable | Notes |
|---|---|
| `SLACK_WEBHOOK_URL` | Incoming webhook URL (`https://hooks.slack.com/services/T…/B…/…`). |

### Optional — for email publishing

| Variable | Notes |
|---|---|
| `EMAIL_FROM` | Sender address (default: `dev-summary@example.com`). |
| `EMAIL_TO_LIST` | Comma-separated recipients (default: `devs@example.com`). |

You'll also need to configure an **SMTP credential** in n8n (Settings → Credentials → Create New → SMTP) and attach it to the `Send Email (SMTP)` node. Any provider works: Gmail app password, SendGrid, Mailgun, AWS SES, your own Postfix.

### Optional — publish toggles

| Variable | Default | Effect when `true` |
|---|---|---|
| `PUBLISH_GITHUB` | `true` (env-unset → evaluated against "true"; to be safe, set explicitly) | Creates a GitHub issue with the summary. |
| `PUBLISH_SLACK` | `false` | Posts the summary to the Slack webhook. |
| `PUBLISH_EMAIL` | `false` | Emails the summary to the dev list. |

**Note on defaults:** the IF nodes compare the env var to the literal string `"true"`. Any value other than exactly `true` makes the false branch run (no-op). To be unambiguous, set every `PUBLISH_*` you intend to use to `true`, and leave the rest unset (or set to `false`).

---

## Customization

### Change the schedule

Open the `Schedule: Mon 9 AM` node. The default cron is `0 0 9 * * 1` (9 AM every Monday, in the workflow timezone). Replace with any cron expression. The workflow `settings.timezone` is set to `America/Mexico_City`; change it under the workflow's **Settings** panel.

### Change the prompt

The `Code: Build prompt` node constructs the prompt sent to Claude. Two things to tweak there:

- **Sections** — the prompt lists exact section headers Claude must use (`## 🚀 Highlights`, etc.). Add, remove, or rename them.
- **Rules** — the bottom of the prompt enforces conciseness, GitHub-flavored markdown, no fabrication. Adjust as needed.

### Use a different Claude model

Open the `Claude API (claude-3-5-sonnet-latest)` node and change `model` in the JSON body. Common alternatives:

- `claude-3-5-sonnet-latest` (default — best quality/cost balance)
- `claude-3-5-haiku-latest` (faster, ~12× cheaper, slightly less nuanced)
- `claude-sonnet-4-5` (newer, if your API access allows it)

Also update `max_tokens` if you expect longer summaries.

### Add or remove data sources

The `Code: Aggregate sources` node pulls from the 4 upstream sources by name (`$('NodeName').first()?.json`). To add another source:

1. Add a new HTTP Request (or another node type) after `Set Date Range`.
2. Wire it into `Code: Aggregate sources`.
3. Extend the aggregation JS to include the new field.
4. Extend the prompt builder in `Code: Build prompt` to reference it.

### Disable Linear / Slack collection

If you never want to try them (don't want the network call at all), just set the node's `On Error` behavior to **Continue (using error output)** and don't wire the error branch — or simply delete the node and update the `Code: Aggregate sources` references.

---

## Cost per run

The dominant cost is the Claude API call. With `claude-3-5-sonnet-latest` at $3/M input tokens and $15/M output tokens:

| Component | Typical token count | Cost |
|---|---|---|
| Input prompt (one week of activity, ~30 PRs + 30 issues + 20 tickets + 20 Slack msgs) | ~6,000–10,000 | $0.018 – $0.030 |
| Output summary (≤600 words markdown) | ~800–1,200 | $0.012 – $0.018 |
| **Total Claude per run** | | **~$0.03 – $0.05** |

The `Code: Extract markdown` node computes the exact cost from the API response's `usage` block and exposes it as `usage.cost_usd` on the final payload. The Slack message includes it in the footer ("cost ~$0.04 USD"), the email body includes it in the small print, and the GitHub issue body ends up containing it as part of the summary text.

Other costs:

- **GitHub REST API**: free for authenticated requests under the 5,000/hr limit.
- **Anthropic API**: see table above.
- **Slack**: incoming webhooks are free.
- **Email**: depends on your SMTP provider (Gmail free within quota, SendGrid free up to 100/day, SES ~$0.10 per 1,000).
- **n8n**: free if self-hosted; cloud has execution-based pricing.

**Realistic run cost: $0.04–$0.06 per week**, dominated by Claude. Negligible unless you're running this on hundreds of repos.

---

## File map

```
bounty-5-n8n/
├── README.md                   # This file
└── weekly-dev-summary.json     # Importable n8n workflow (active: false)
```

The JSON is plain n8n export format — no transformations needed. Drop it into n8n via **Import from File**.

---

## Troubleshooting

**"No data" in the summary even though GitHub has activity.**
The Search API returns PRs/Issues updated in the window, not created. If your team is slow to update issues, switch to filtering on `created:` instead of `updated:` in the two GitHub HTTP nodes. (Or split into two queries and merge.)

**"Claude returned 401".**
`ANTHROPIC_API_KEY` is missing or invalid. Check n8n → Settings → Variables, then re-execute.

**"GitHub returned 403 — rate limit exceeded".**
The Search API has a 30 req/min/hour limit per token. Either upgrade to a fine-grained PAT with higher limits or space out executions.

**"Slack post failed: invalid_blocks".**
The summary exceeds Slack's 3,000-char section limit. The Slack node already truncates at 2,800 chars, so this should be rare. If it happens, lower the prompt's word limit or split into multiple blocks.

**"The IF nodes all went to the no-op branch even though I set the env var."**
The comparison is strict-equals against the literal string `"true"`. Make sure there's no extra whitespace, no quotes around `true`, and the variable is set at the workflow level (not just the node level).

---

## License

MIT — use, modify, sell, ship. Attribution appreciated but not required.
