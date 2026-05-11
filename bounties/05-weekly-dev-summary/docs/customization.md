# Customization

## Switch delivery to Discord

Replace the **Post to Slack** node's body with:

```json
{ "content": {{ JSON.stringify($json.text) }} }
```

…and point `SLACK_WEBHOOK_URL` at your Discord channel webhook (Discord accepts the same POST pattern; rename the env var if you want).

## Switch delivery to Email

Delete **Post to Slack**, add n8n's built-in **Send Email** node:

- To: your team alias
- Subject: `Weekly Dev Summary — {{ $('Aggregate Activity').item.json.repo }}`
- Body (HTML): `={{ $json.text }}` (run through a markdown→HTML node if you want rendered output)

## Change cadence

Edit the trigger's cron expression:

- Daily 9am: `0 9 * * *`
- Mondays 8am: `0 8 * * 1`
- Twice weekly (Mon + Thu 5pm): two trigger nodes or `0 17 * * 1,4`

## Multi-repo digest

Two clean approaches:

1. **Per-repo workflow**: clone the workflow, set a different `GITHUB_REPO`. Cheapest mental model.
2. **Fan-out**: replace `Config` with a "Split In Batches" node fed a list of repos, loop the three GitHub calls per repo, accumulate, then send one mega-prompt to Claude. Use only if you want a single combined narrative.

## Adjust the Claude prompt

Edit the `Claude Summarize` node's `jsonBody`. Knobs worth tuning:

- `max_tokens` (default 1500) — bigger for verbose digests
- Persona / tone in the user message
- `commits.slice(0,50)` — raise the cap for very active repos (watch token cost)

## Cost note

A single weekly run touches ~5–15K input tokens + ~1K output. With `claude-sonnet-4-20250514` (~$3/M in, $15/M out) that's roughly **$0.02–0.05 per run** — call it a couple bucks a year per repo.
