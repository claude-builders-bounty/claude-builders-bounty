# Weekly Dev Summary — n8n + Claude

An n8n workflow that every Friday at 17:00 fetches the week's GitHub activity
(commits, closed issues, merged PRs), asks Claude to write a narrative
summary, and posts it to Slack.

Deliverable for bounty #5.

## Import

1. In n8n: **Workflows → ⋯ → Import from File**
2. Select `weekly-dev-summary.workflow.json`
3. Done — the workflow appears prewired.

## Configure (5 steps)

1. Open the **Config (edit me)** node — every variable lives there:

   | Variable | Purpose |
   |---|---|
   | `github_repo` | `owner/repo` to summarize |
   | `slack_webhook_url` | Incoming Slack webhook URL |
   | `claude_api_key` | Anthropic API key |
   | `language` | `en` or `fr` (use plain `en`/`fr`; the prompt maps `fr`→French) |
   | `claude_model` | default `claude-sonnet-4-20250514` |
   | `github_token` | optional but recommended (60 → 5000 req/h) |

2. Activate the workflow (top-right toggle) — the Schedule Trigger runs it
   every **Friday at 17:00 UTC**.
3. Test one run: click **Execute Workflow** (uses the same data fetches).
4. Check Slack for the posted summary.
5. Adjust `triggerAtDay` / `triggerAtHour` in the Schedule Trigger node to
   change the day/time; set `Settings → Timezone` for local time.

## Delivery channel

The final node posts to a Slack incoming webhook (no OAuth app needed).
To deliver by email instead: delete **Send to Slack** and add an
**Email (SMTP)** node — body: `{{ $json.summary }}` — with your SMTP
credentials. The **Extract Text** node output carries `summary`, `repo`, and
`slack_webhook_url` either way.

## Nodes

| Node | Role |
|---|---|
| Schedule Trigger | weekly cron, Friday 17:00 |
| Set (Config) | all tunables in one place |
| HTTP × 3 | GitHub API: commits (since 7d), closed issues, closed PRs |
| Code (Aggregate) | merges the three feeds, filters to the last 7 days, ships stats |
| HTTP (Claude) | Anthropic Messages API call, model + language from config |
| Code (Extract Text) | pulls text out of the Claude response |
| HTTP (Slack) | posts to the webhook |

## Verified execution

The workflow was imported into n8n 1.x, executed with "Execute Workflow"
against a live repo, and the Friday 17:00 trigger confirmed armed after
activation. The Claude node returned the narrative summary and the Slack
node posted it successfully.

> Note: the workflow exports without live credentials. First run shows
> "credential missing" style errors on the Claude node until
> `claude_api_key` is filled in **Config (edit me)** — that's the only
> required edit.
