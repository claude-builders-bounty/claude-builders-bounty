# Weekly GitHub Digest (n8n workflow)

An n8n workflow that summarizes a GitHub repository's week — commits, closed
issues, merged PRs — as a narrative written by the Claude API, delivered to a
Slack/Discord webhook every Friday at 5pm.

## Setup (5 steps)

1. **Import the workflow**: n8n → Workflows → *Import from File* → select
   `weekly-github-digest.json`.
2. **Create the Anthropic credential**: Credentials → *Header Auth* → name it
   `Anthropic API Key`, header name `x-api-key`, value `sk-ant-...` (your
   Anthropic API key). The *Claude summary* node references it.
3. **Open the Config node** and set three values:
   - `repo` — `owner/name` of the repository to digest
   - `language` — `EN` or `FR`
   - `webhookUrl` — your Slack/Discord incoming-webhook URL
4. **Activate** the workflow (top-right toggle). The Schedule Trigger fires
   Fridays at 17:00 in the n8n instance's timezone.
5. **Test now**: open the *Weekly Trigger* node → *Execute step* (or use the
   *Test workflow* button) to run the whole chain immediately.

## What it does

```
Weekly Trigger (Fri 5pm)
  └─ Config                repo / language / webhookUrl / week-start (auto)
      └─ Fetch commits     GET /repos/{repo}/commits?since=Monday
          └─ Fetch closed issues   GET /repos/{repo}/issues?state=closed&since=Monday
              └─ Fetch merged PRs  GET /repos/{repo}/pulls?state=closed&sort=updated
                  └─ Build digest  combines all three into an LLM prompt
                      └─ Claude summary  claude-sonnet-4-20250514 → narrative
                          └─ Deliver to webhook  POST { text, repo, counts }
```

- The week starts Monday 00:00 UTC, computed in the Config node.
- The three fetch nodes have **Execute Once** enabled (`executeOnce: true`) —
  without it, n8n runs each HTTP node once per input item and the item count
  multiplies down the chain (5 commits → 5 issue requests → 15 items → …).
- The `/issues` endpoint returns closed PRs mixed in; the Build digest Code
  node keeps only real issues (no `pull_request` key). The `/pulls` endpoint
  returns closed PRs; the Code node keeps only those with `merged_at` set
  within the week.
- The URL parameters use n8n's canonical `=`-prefixed expression form, which
  evaluates both on UI import and on workflows created via the REST API.
- The prompt instructs the model for a 150–250 word narrative: what shipped,
  what was fixed, notable commits, one honest momentum sentence.
- The webhook payload: `{ "text": "<narrative>", "repo": "...", "counts":
  { "commits": N, "issues": N, "prs": N } }` — matches the Slack
  `text` field shape; works unchanged on Discord webhooks too.

## Configuration reference

| Field | Where | Values |
|---|---|---|
| Schedule | Weekly Trigger node | `0 17 * * 5` — Fridays 17:00; edit the cron expression |
| Repo | Config node | any public or private repo the GitHub API can read |
| Language | Config node | `EN` (English) or `FR` (français) |
| Destination | Config node | any URL accepting JSON POST (Slack, Discord, custom) |
| Model | Claude summary node | `claude-sonnet-4-20250514`; swap for any Anthropic model |

Private repos: add a GitHub credential (fine-grained PAT, `contents:read`)
to the three Fetch nodes, or set the `Authorization: Bearer` header.

## Tested

See `examples/PROVENANCE.md` — the workflow was executed on a local n8n
instance against a live public repository; the Claude endpoint was redirected
to a local mock (no API key in the test environment) and the webhook to a
local catcher. Screenshot of the successful execution included.
