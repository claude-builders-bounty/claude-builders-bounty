# Claude Weekly Dev Digest (n8n workflow)

A weekly cron that reads a GitHub repo's activity for the past 7 days — commits, closed
issues and merged PRs — has Claude write a short narrative digest, and posts it to Discord
or Slack.

```
Fri 17:00 → Config → Collect GitHub → Claude Summary → Extract → Deliver
```

## Setup (5 steps)

1. In n8n: **Workflows → Import from File** → select `workflow.json`.
2. Set two environment variables on your n8n instance:
   - `ANTHROPIC_API_KEY` — **required** (console.anthropic.com)
   - `GITHUB_TOKEN` — optional; raises GitHub's rate limit and reads private repos
3. Open the **Config** node and fill three fields: `repo_owner`, `repo_name`, and
   `discord_webhook`. For Discord: *Channel → Integrations → Webhooks → New Webhook*.
   For Slack: an *Incoming Webhook* URL works in the same field with no changes.
4. Set `language` to `en` or `fr`. Change `days` if you want a different window.
5. **Activate** the workflow. It fires Fridays at 17:00. Click **Execute Workflow** once to
   see it end-to-end.

## Config fields

| Field | Meaning | Example |
|---|---|---|
| `repo_owner` | GitHub user or org | `n8n-io` |
| `repo_name` | Repository | `n8n` |
| `discord_webhook` | Discord **or** Slack incoming webhook URL | `https://discord.com/api/webhooks/...` |
| `language` | Summary language | `en` or `fr` |
| `days` | Look-back window | `7` |

## Design notes

- **Secrets stay out of the JSON** — both keys come from the n8n environment, so the
  exported file is safe to share.
- **One delivery node serves Discord and Slack**: it sends both `content` (Discord) and
  `text` (Slack); each platform ignores the field it doesn't use.
- **No database, Docker, or extra services** — only GitHub and the Claude API.
- Every GitHub call is wrapped so a rate-limit or 404 degrades to an empty list instead of
  failing the run.
- `claude-sonnet-4-20250514`, `max_tokens: 1200`, prompt constrained to "invent nothing".

## Verify

```
node verify.mjs
```

Asserts the trigger cron, the three GitHub queries, the Claude call, EN/FR, webhook
delivery, env-based secrets, linear wiring, that every embedded Code node parses, and — as
regression guards for the two import bugs real n8n exposed — that the workflow carries a
top-level `id` and a `meta` block.

It also **executes the GitHub-collection node for real** against a stubbed `httpRequest`, so
the parts that a syntax check cannot see are covered: that PRs returned by the issues endpoint
are filtered out of the issue count, that unmerged and out-of-window PRs are dropped, that the
prompt is assembled with the right repo and word limit, that `language: fr` switches the
prompt, that a rate-limited/404ing GitHub call degrades to an empty list instead of killing
the run, and that the `Authorization` header appears only when `GITHUB_TOKEN` is set.

## Imported and round-tripped on a real n8n (2.22.6)

Not just validated as JSON — actually imported by the n8n CLI:

```
N8N_USER_FOLDER=<folder> npx --yes n8n import:workflow --input=workflow.json
N8N_USER_FOLDER=<folder> npx --yes n8n export:workflow --id=claudeWeeklyDigest1 --output=roundtrip.json
```

The first import attempt failed with a real error — `SQLITE_CONSTRAINT: NOT NULL constraint
failed: workflow_entity.id` — because the workflow had no top-level `id`. Adding
`"id": "claudeWeeklyDigest1"` fixed it (`Successfully imported 1 workflow`), and the export
round-trip returns the workflow intact. Both are now asserted by `verify.mjs`. A screenshot
of the imported workflow open in the editor (`screenshot.png`), all six nodes wired on the
canvas, is attached as evidence.

## Notes / limitations

- Public repos need no token; private repos need `GITHUB_TOKEN`.
- GitHub's `issues` endpoint also returns PRs — they're filtered out of the issue count.
- Activity is capped at 30 items per section to keep the prompt cheap.
