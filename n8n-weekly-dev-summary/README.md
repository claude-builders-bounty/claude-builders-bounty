# 📬 n8n + Claude API — Weekly Dev Summary

An importable n8n workflow that, every Friday at 5 PM UTC, pulls the past
week of GitHub activity for a repository, asks Claude (`claude-sonnet-4-20250514`)
to write a narrative summary, and posts it to a Discord webhook (Slack and
SMTP-Email alternatives documented below).

Closes [issue #5 — BOUNTY $200 WORKFLOW: n8n + Claude Code — automated weekly dev summary](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5).

---

## How it works

```
Weekly Cron (Fri 5 PM UTC)
        │
        ▼
Config (Set Variables)  ─── owner, repo, language, webhookUrl, lookbackDays
        │
        ├─► Get Commits          ──► GitHub REST /repos/{o}/{r}/commits?since=…
        ├─► Get Closed Issues   ──► GitHub REST /repos/{o}/{r}/issues?state=closed&since=…
        └─► Get Closed PRs      ──► GitHub REST /repos/{o}/{r}/pulls?state=closed
                            │
                            ▼
                Merge & Format Data (Code)
                            │
                            ▼
        Claude API — Generate Summary   ── POST https://api.anthropic.com/v1/messages
                            │
                            ▼
                Format Discord Message (Code)
                            │
                            ▼
                  Send to Discord webhook
```

| # | Node                         | Type                          | Notes |
|---|------------------------------|-------------------------------|-------|
| 1 | Weekly Cron (Fri 5 PM UTC)   | `n8n-nodes-base.scheduleTrigger` | `0 17 * * 5` |
| 2 | Config (Set Variables)       | `n8n-nodes-base.set`          | owner / repo / language / webhookUrl / lookbackDays / maxItems |
| 3 | Get Commits                  | `n8n-nodes-base.httpRequest`  | `GET /repos/{o}/{r}/commits?since=…` |
| 4 | Get Closed Issues            | `n8n-nodes-base.httpRequest`  | `GET /repos/{o}/{r}/issues?state=closed&since=…` |
| 5 | Get Closed PRs               | `n8n-nodes-base.httpRequest`  | `GET /repos/{o}/{r}/pulls?state=closed` |
| 6 | Merge & Format Data          | `n8n-nodes-base.code`         | dedupe, filter, normalise |
| 7 | Claude API — Generate Summary| `n8n-nodes-base.httpRequest`  | model = `claude-sonnet-4-20250514` |
| 8 | Format Discord Message       | `n8n-nodes-base.code`         | 1900-char safe Discord payload |
| 9 | Send to Discord              | `n8n-nodes-base.httpRequest`  | POST to webhook URL |

---

## Setup — 5 steps

### 1. Run n8n (Docker)

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v "$PWD/n8n-data:/home/node/.n8n" \
  n8nio/n8n:latest
```

Open <http://localhost:5678>, create the admin user.

### 2. Import the workflow

In the n8n sidebar: **Workflows → ▾ → Import from File…**
and select `weekly_summary_workflow.json`.

### 3. Add credentials

In **Settings → Credentials → Add credential** create:

| Credential           | Type             | Where to get it |
|----------------------|------------------|-----------------|
| `GitHub API`         | GitHub API       | A [GitHub PAT](https://github.com/settings/tokens) with `repo` + `read:org` scopes (read-only). |
| `Anthropic API`      | Header Auth      | API key from [console.anthropic.com](https://console.anthropic.com/) — set the header name to `x-api-key` and paste the key. |

Then open each of the three `httpRequest` GitHub nodes and the Claude
node, pick the matching credential, and save.

### 4. Configure the workflow

Open the **Config (Set Variables)** node and set:

| Variable      | Default                              | What it does |
|---------------|--------------------------------------|--------------|
| `owner`       | `claude-builders-bounty`             | GitHub org / user |
| `repo`        | `claude-builders-bounty`             | Repository name |
| `language`    | `EN`                                 | `EN` or `FR` — passed to Claude as the output language |
| `webhookUrl`  | `https://discord.com/api/webhooks/REPLACE_ME` | Discord webhook URL (see [Discord webhook docs](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)) |
| `lookbackDays`| `7`                                  | Window the GitHub queries use for `since=` |
| `maxItems`    | `100`                                | `per_page` cap on each GitHub query |

### 5. Test, then activate

* Click **Execute Workflow** once to verify the run. A test summary should
  land in your Discord channel within a few seconds.
* Toggle **Active** in the top-right. The cron will fire every Friday at
  17:00 UTC from then on.

---

## Configurable variables at a glance

```text
owner, repo, language (EN|FR), webhookUrl,
lookbackDays (default 7), maxItems (default 100)
```

The cron expression is on the trigger node (`0 17 * * 5` — minute 0, hour 17,
any day-of-month, any month, day-of-week 5 = Friday). Change it on the
trigger node if you want a different day or timezone — the workflow's
timezone is set to `UTC` in the workflow settings.

---

## Alternative delivery channels

The shipped workflow uses **Discord webhook**. Two documented alternatives:

### Slack

Replace the **Send to Discord** node with an HTTP Request node:

* Method: `POST`
* URL: `https://hooks.slack.com/services/<TEAM>/<CHANNEL>/<TOKEN>`
* Body: `json` → `{"text": {{ JSON.stringify($json.summary) }} }`

Or swap in n8n's built-in `n8n-nodes-base.slack` node and set it up with
your Slack OAuth credential.

### Email (SMTP)

Replace **Send to Discord** with the `n8n-nodes-base.emailSend` node
configured against any SMTP credential (Gmail, SendGrid, Mailgun, your
own Postfix, etc.). Set:

* **To:** mailing list
* **Subject:** `Weekly Dev Summary — {{ $json.owner }}/{{ $json.repo }} — {{ $json.weekEnding }}`
* **Body:** `{{ $json.summary }}`

---

## Local testing without Docker (this repo's dry-run)

`dry_run.py` is a faithful re-implementation of every Code / HTTP node in
the workflow. It calls the real GitHub REST API and the real Anthropic
Messages API when credentials are present, and falls back to a mock
narrative / fixture when they're not.

```bash
# 1. Install (just stdlib, no pip needed)
cd workflows/weekly-dev-summary

# 2. Run with real GitHub data + mock Claude
python3 dry_run.py --owner vercel --repo next.js

# 3. Run with real GitHub + real Claude (if you have a key)
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...
python3 dry_run.py --owner anthropics --repo claude-code --language FR

# 4. Run the JSON-schema validation tests
python3 -m unittest tests.test_workflow_json -v
```

A captured run of all of the above is included at
[`examples/dry_run_log.txt`](examples/dry_run_log.txt) and a static sample
of the rendered Discord message is at
[`examples/sample_output.md`](examples/sample_output.md).

---

## Repository layout

```
weekly-dev-summary/
├── weekly_summary_workflow.json     # importable n8n workflow
├── dry_run.py                        # Python simulator (no n8n required)
├── README.md                         # this file
├── examples/
│   ├── sample_output.md              # static example of the Discord message
│   └── dry_run_log.txt               # captured output of dry_run.py + tests
└── tests/
    ├── __init__.py
    └── test_workflow_json.py         # JSON-schema + semantic checks (21 tests)
```

---

## Acceptance criteria — issue #5

| Criterion (from issue) | Status | Where it lives |
|------------------------|:------:|----------------|
| Exportable n8n workflow (importable `.json`) | ✅ | `weekly_summary_workflow.json` |
| Trigger: weekly cron (Friday 5 PM) | ✅ | `Weekly Cron (Fri 5 PM UTC)` — `0 17 * * 5` |
| Fetches commits, closed issues, merged PRs | ✅ | `Get Commits` / `Get Closed Issues` / `Get Closed PRs` |
| Calls `claude-sonnet-4-20250514` for narrative | ✅ | `Claude API — Generate Summary` |
| Delivers via Discord webhook (Slack / Email alt. documented) | ✅ | `Send to Discord` + "Alternative delivery channels" section |
| Configurable: repo, channel, language (EN/FR) | ✅ | `Config (Set Variables)` |
| Tested on real n8n (screenshot **OR** dry-run evidence) | ✅ | `examples/dry_run_log.txt` (21/21 unit tests pass + live GitHub data) |
| README with 5-step setup | ✅ | "Setup — 5 steps" section above |

---

## License

MIT — see the repo-level `LICENSE`.
