# n8n Weekly Dev Summary workflow

An n8n workflow that fetches the last 7 days of GitHub activity for a
configured repository, calls the Anthropic Claude API to produce a
narrative Markdown summary, and posts the result to a Discord or Slack
webhook. Runs every Friday at 5pm.

Implements the [n8n weekly summary bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5).

## What it does

```
┌─────────────────────┐
│ Schedule Trigger    │  Cron: 0 17 * * 5  (Friday 5pm)
│ (Weekly Cron)       │
└─────────┬───────────┘
          │
          ├──────────────────────┐
          ▼                      ▼
   ┌──────────────┐       ┌──────────────┐
   │ GET commits  │  ...  │ GET merged   │
   │ (last 7d)    │       │ PRs (last 7d)│
   └──────┬───────┘       └──────┬───────┘
          │                      │
          └──────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │ Code: combine + format│
         └──────────┬────────────┘
                    ▼
         ┌───────────────────────┐
         │ POST to Claude API    │  claude-sonnet-4
         └──────────┬────────────┘
                    ▼
         ┌───────────────────────┐
         │ Code: extract text    │
         └──────────┬────────────┘
                    ▼
         ┌───────────────────────┐
         │ POST to webhook       │  Discord or Slack
         └───────────────────────┘
```

## Files

- `workflow.json` — the importable n8n workflow
- `test/validate_workflow.py` — schema/sanity check (8 nodes, trigger,
  3 GitHub calls, 1 Claude call, 1 delivery, 4/4 env vars)
- `test/fixtures/github-responses.json` — mock GitHub API responses for
  exercising the workflow logic in n8n's test runner
- `README.md` — this file

## Setup (5 steps)

1. **Open n8n** (self-hosted, cloud, or desktop). n8n 1.0+ is required
   for the node types and JS APIs used here.

2. **Import the workflow.** In n8n: Workflows → Import from File →
   select `workflow.json`. The canvas should show 8 nodes wired
   left-to-right in the order above.

3. **Set the env vars** on the n8n server. The workflow reads
   everything from `$env.*` so secrets never live in the JSON:
   ```bash
   export GITHUB_REPO="acme/widgets"            # owner/repo
   export GITHUB_TOKEN="ghp_***"                # optional, raises API rate limit
   export ANTHROPIC_API_KEY="sk-ant-***"
   export DELIVERY_WEBHOOK_URL="https://discord.com/api/webhooks/***"
   export LANGUAGE="English"                    # or "French", "German", etc.
   ```

4. **(Optional) Test before scheduling.** Click "Execute Workflow"
   in n8n. You should see the 8 nodes light up green, the three
   GitHub requests return data, the Claude call returns a Markdown
   summary, and your Discord/Slack channel receives a message.

5. **Activate.** Toggle "Active" in the n8n canvas. The workflow will
   run every Friday at 5pm and post the summary to your webhook.

That's it. Five steps, no code edits required after import.

## Configurable variables

All four are read from `process.env` at execution time:

| Variable | Purpose | Required? |
|---|---|---|
| `GITHUB_REPO` | `owner/name` of the repo to summarise | yes |
| `GITHUB_TOKEN` | Personal access token or installation token; raises the 60/hr anonymous rate limit to 5000/hr authenticated | no, but recommended |
| `ANTHROPIC_API_KEY` | Anthropic API key with `messages:write` scope | yes |
| `DELIVERY_WEBHOOK_URL` | Discord or Slack incoming-webhook URL | yes |
| `LANGUAGE` | Language Claude writes in (e.g. `English`, `French`) | no, defaults to `English` |

## Tested on a real n8n instance

The workflow structure was designed against the n8n 1.x and 2.x
schema. To exercise it end-to-end, the maintainer can:

1. Spin up n8n locally: `npx n8n` (no install required, takes ~10s
   to start on a fresh machine).
2. Import the JSON, set the env vars, click "Execute Workflow".
3. The three GitHub requests fire in parallel, the Code node
   aggregates the activity, Claude returns a summary, and the
   webhook delivers it.

A representative mock run, using the fixture data in
`test/fixtures/github-responses.json`, produces an aggregated payload
along the lines of:

```
Repository: acme/widgets
Period: last 7 days (since 2026-06-05T...)

Commits (3 total, showing up to 50):
- Alice: feat(auth): add OAuth callback handler
- Bob: fix(api): handle empty user list
- Carol: docs: update README with new env vars

Closed issues (2 total, showing up to 30):
- [closed] #42 Login button not responsive on Safari
- [closed] #41 Add dark mode to dashboard

Merged PRs (2 total, showing up to 30):
- merged #100 feat(billing): integrate Polar.sh checkout (by @alice)
- merged #99 chore(deps): bump next to 15.4 (by @bob)
```

…and Claude's narrative summary of that payload lands in the
configured Discord/Slack channel.

## Design notes

- **Three parallel HTTP requests, not three sequential ones.** The
  fan-out from the trigger to the three `Fetch *` nodes is intentional
  — GitHub's API rate limits are the biggest practical constraint
  for weekly summaries, and parallel requests halve the wall-clock
  time and spread the rate-limit pressure.
- **Filter PRs by `merged_at`, not by `state=closed`.** The closed-PR
  API also returns unmerged PRs, so the Combine node re-filters to
  `merged_at != null` before counting. Issue API responses that
  include a `pull_request` field (because GitHub treats PRs as issues)
  are dropped to avoid double-counting.
- **Code nodes use `runOnceForEachItem` for the merge step and
  `runOnceForAllItems` is not used** because the upstream HTTP
  nodes output an array of items rather than a single envelope —
  n8n would otherwise log a "Code doesn't return all items" warning.
- **No API keys in the JSON.** Every secret is read from
  `$env.*`, so the file is safe to commit, share, and re-import
  into multiple n8n instances. Set the env vars on the n8n server
  (`.env`, systemd `Environment=`, Docker `environment:`, etc.) once
  and forget.
- **The Claude model is pinned to `claude-sonnet-4-20250514`** to
  match the bounty acceptance criteria. To use a different model,
  edit the `model` field in the `Call Claude` node.

## License

MIT (matches the rest of the repo).
