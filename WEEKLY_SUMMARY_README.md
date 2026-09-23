# n8n + Claude — automated weekly dev summary

Drop-in n8n workflow that:

1. Runs on a schedule (default: every Friday 17:00)
2. Pulls the last week's **commits**, **closed issues** and **merged PRs** from a GitHub repo
3. Asks Claude to turn them into a concise leadership update (EN or FR)
4. Posts the summary as a comment on a pinned "Weekly Dev Summary" GitHub issue
5. (Optional) pings a Slack channel via incoming webhook

## Setup (5 steps)

1. **Import the workflow** — in n8n, *Workflows → Import from File* → pick
   `workflow.json`.
2. **Set environment variables** — copy `.env.example` and fill in the
   values, then set them on the n8n instance:
   - Self-hosted: pass them when starting the container (`docker run -e …`)
     or via your process manager / `.env`.
   - n8n Cloud: *Instance Settings → Environment Variables*.
   - **Self-hosted note:** n8n ≥ 1.4x blocks `$env` inside nodes by default.
     Keep `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` set, or the workflow's
     `{{ $env.… }}` expressions will be empty.
   - Required: `ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`,
     `GITHUB_TOKEN`, `WEEKLY_SUMMARY_REPO_URL`, `WEEKLY_SUMMARY_ISSUES_URL`,
     `WEEKLY_SUMMARY_PRS_URL`, `GITHUB_REPORT_URL`.
     Optional: `SUMMARY_LANGUAGE` (default `EN`, or `FR`),
     `SLACK_WEBHOOK_URL` (empty = Slack step is skipped).
3. **No credentials needed** — every HTTP node carries its own
   `Authorization` / `x-api-key` header from `$env`, so n8n credential
   entries are not required.
4. **Adjust the schedule / prompt** — the trigger defaults to *Every Friday
   17:00*; the "Build Claude prompt" Code node holds the summary prompt
   (sections, word count, language).
5. **Test run** — hit *Execute workflow* once (or trigger a manual run) and
   check that the target GitHub issue gets a new comment.

## What a run produces

The Claude response is plain Markdown, posted verbatim as an issue comment:

```markdown
**What shipped**
- **Pre-Tool-Use Hook**: added safety interceptors for destructive shell
  commands (#3).

**What changed**
- 14 commits on main, mostly docs and CI cleanup.

**What was closed**
- #7 flaky CI on macOS runners
- #12 update README badges

**Follow-ups / risks**
- #9 (rate limiting) is still open and blocks the public beta.
```

If the week has no activity, the summary says so explicitly instead of
inventing content.

> **Verification endpoint note:** the run above was verified through a
> self-hosted Anthropic-compatible proxy (cost savings for testing) —
> `ANTHROPIC_BASE_URL` pointed at a local proxy. The workflow uses the
> standard Anthropic Messages API, so switching to the official
> `api.anthropic.com` with a real `sk-ant-…` key is a one-line env
> change; no workflow modification is needed.

## Tuning

- **Different cadence** — change the schedule trigger (daily, bi-weekly, …).
- **Different model** — set `CLAUDE_MODEL` (any model the endpoint serves).
- **Different Claude endpoint** — set `ANTHROPIC_BASE_URL` to any
  Anthropic-compatible API base (direct API or a local proxy).
- **Different output** — point "Post to GitHub issue" at a different URL.
  The summary is plain Markdown; any Markdown renderer works.
- **Longer history** — bump `per_page=30` to `per_page=100` in the three
  feed URLs, or add a second HTTP node that paginates.

## Error handling built in

- Every HTTP node retries on failure (GitHub: 3× / 3 s, Claude: 5× / 10 s,
  post/Slack: 3× / 5 s) — transient 503/429s are absorbed automatically.
- The Claude call has a 5-minute request timeout for slow upstreams.
- The three feeds are de-duplicated in the prompt builder (a merged PR shows
  up in both the `issues` and `pulls` endpoints; only one line is emitted).
- The Slack step is an `If` branch on `SLACK_WEBHOOK_URL` — an empty value
  skips it silently.

## Cost

One run = 1 Claude call (≈2 k tokens in, ≈1 k out). A weekly cadence is
trivial cost; even a daily run stays small.
