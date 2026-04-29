# n8n Weekly Dev Summary Workflow

An n8n workflow that generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

## Features

- **Weekly cron trigger** — runs every Friday at 5pm (configurable)
- **GitHub API fetch** — collects commits, closed issues, and merged PRs from the past 7 days
- **Claude narrative** — calls `claude-sonnet-4-20250514` to produce a concise, engaging weekly summary
- **Dual delivery** — sends via Discord webhook **or** email (SMTP)
- **Configurable** — repo, language (EN/FR), and delivery method are workflow variables

## Setup (5 steps)

1. **Import the workflow** — In n8n, go to Workflows → Import from File → select `weekly-dev-summary.json`

2. **Configure GitHub credentials** — Go to Credentials → New → Header Auth. Name it "GitHub Token", set header name to `Authorization` and value to `Bearer <your-github-pat>`. Then edit each HTTP Request node and select this credential.

3. **Configure Claude API credentials** — Go to Credentials → New → Anthropic API. Enter your API key. Then edit the "Claude Narrative" node and select this credential.

4. **Set workflow variables** — Click the workflow settings gear icon → Variables, and update:
   - `GITHUB_REPO` — e.g. `owner/repo`
   - `DELIVERY_METHOD` — `discord` or `email`
   - `LANGUAGE` — `EN` or `FR`
   - For Discord: add a Discord Webhook credential and update the "Send to Discord" node
   - For Email: add an SMTP credential and set `EMAIL_FROM` / `EMAIL_TO` variables

5. **Activate the workflow** — Click the Active toggle in the top-right corner. It will now run every Friday at 5pm. You can also click "Execute Workflow" to test immediately.

## Workflow Diagram

```
Every Friday 5pm
  ├── Fetch Commits ──────┐
  ├── Fetch Closed Issues ─┤──→ Aggregate Data ──→ Claude Narrative ──→ Format Message ──→ Delivery Method?
  └── Fetch Merged PRs ───┘                                                                ├── Discord
                                                                                            └── Email
```

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `GITHUB_REPO` | `owner/repo` | GitHub repository in `owner/repo` format |
| `GITHUB_API_URL` | `https://api.github.com` | GitHub API base URL (change for GHES) |
| `DELIVERY_METHOD` | `discord` | `discord` or `email` |
| `LANGUAGE` | `EN` | `EN` for English, `FR` for French |
| `EMAIL_FROM` | `noreply@example.com` | Sender address (email mode) |
| `EMAIL_TO` | `team@example.com` | Recipient address (email mode) |

## Credentials Required

| Credential | Type | Used By |
|---|---|---|
| GitHub Token | Header Auth (`Authorization: Bearer <pat>`) | Fetch Commits, Fetch Closed Issues, Fetch Merged PRs |
| Anthropic API | Anthropic API Key | Claude Narrative |
| Discord Webhook | Discord Webhook URL | Send to Discord (if selected) |
| SMTP Account | SMTP host/port/user/pass | Send via Email (if selected) |

## Extending

- **Add Slack delivery** — Duplicate the Discord branch, swap the node for `n8n-nodes-base.slack`, and update the IF condition
- **Multiple repos** — Add a Split In Batches node before the HTTP requests and set `GITHUB_REPO` per batch
- **Custom cron** — Edit the Schedule Trigger node's cron expression (default: `0 17 * * 5`)

Generated/reviewed with: claude-opus-4-6