# Weekly Dev Summary — n8n + Claude Workflow

An **importable n8n workflow** that automatically generates a clear, narrative
weekly summary of your GitHub repository activity using the **Claude API**, and
delivers it to Slack, Discord, or Email/SMTP every Friday at 5 PM.

---

## What It Does

Every Friday at 17:00 (configurable), the workflow:

1. Fetches the last 7 days of **commits**, **closed issues**, and **merged PRs**
   from your GitHub repository via the GitHub REST API
2. Aggregates the data and builds a structured prompt
3. Sends the prompt to **Claude** (`claude-sonnet-4-20250514`) to generate a
   readable 3-5 paragraph narrative summary
4. Delivers the summary to **Slack**, **Discord**, or **Email/SMTP** (your choice, set via env var)

---

## Setup (5 steps)

### Step 1 — Import the workflow

In your n8n instance, go to **Workflows → Import from File**, select `workflow.json`.

### Step 2 — Set your n8n Variables

In n8n, go to **Variables** (or use a `.env` on self-hosted) and set:

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | `owner/repo` to monitor | `my-org/backend-api` |
| `GITHUB_TOKEN` | GitHub Personal Access Token (read-only, `repo` scope) | `ghp_xxx...` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-xxx...` |
| `DELIVERY_CHANNEL` | `slack`, `discord`, or `email` | `slack` |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL (if using Slack) | `https://hooks.slack.com/...` |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL (if using Discord) | `https://discord.com/api/webhooks/...` |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `SMTP_TO` | SMTP credentials (if using email delivery) | see CONFIGURATION.md |
| `SUMMARY_LANGUAGE` | `EN` or `FR` (default: `EN`) | `EN` |

### Step 3 — Activate the workflow

Toggle the workflow to **Active**. It will run automatically every Friday at 17:00.

### Step 4 — Test manually

Click **"Test workflow"** or use the **Execute** button to run it immediately and
verify the output in your Slack/Discord channel or inbox.

### Step 5 — (Optional) Customise the schedule

Click the **"Every Friday at 5 PM"** node and change the cron expression:
- `0 17 * * 5` = Fridays at 17:00 UTC
- `0 9 * * 1` = Mondays at 09:00 UTC (Monday morning standup)

---

## Workflow Architecture

```
[Cron Trigger: Friday 5PM]
         │
[Set Config Variables]
    ┌────┤────┐
    │         │         │
[Fetch     [Fetch     [Fetch
 Commits]   Issues]    PRs]
    └────┬────┘
         │
[Aggregate GitHub Data (Code)]
         │
[Build Claude Prompt (Code)]
         │
[Call Claude API (HTTP)]
         │
[Format Final Message (Code)]
         │
[Route by Delivery Channel (IF)]
    ┌────┼────┐
[Slack] [Discord] [Email/SMTP]
```

---

## Sample Output

```markdown
## 📊 Weekly Dev Summary — my-org/backend-api
**Period:** 2026-03-24 → 2026-03-31

**Stats:** 23 commits · 4 PRs merged · 7 issues closed · 5 contributors

This was a productive week focused on observability and API stability.
The team merged four pull requests, most notably the Prometheus metrics endpoint
(#142) that gives us real-time visibility into request latency and error rates
across all services.

Seven issues were resolved, including the long-standing race condition in the
session handler (#138) and a null-pointer bug in the configuration loader (#140).
The rate limiting middleware (#144) deserves special mention — it arrived just
ahead of a planned load test and should prevent the API from being overwhelmed
under traffic spikes.

Five engineers contributed commits this week, with particular activity around
the auth and monitoring subsystems. The CI pipeline also received attention,
now running on Ubuntu 22.04 with improved caching that cuts build time by ~40%.

With the metrics and rate limiting foundations in place, the team is well-positioned
to begin the performance optimisation sprint next week.
```

---

## Requirements

- n8n v1.0+ (self-hosted or n8n Cloud)
- GitHub Personal Access Token with `repo` scope (read-only)
- Anthropic API key (`claude-sonnet-4-20250514`)
- Slack Incoming Webhook URL, Discord Webhook URL, or SMTP credentials (one required)

---

## Customisation

- **Change the Claude model**: Edit the `Call Claude API` node's `body.model` field
- **Change the language**: Set `SUMMARY_LANGUAGE=FR` for French summaries
- **Use email delivery**: Set `DELIVERY_CHANNEL=email` and configure the SMTP variables — see [CONFIGURATION.md](CONFIGURATION.md)
- **Monitor multiple repos**: Duplicate the workflow and set different `GITHUB_REPO`
  variables

---

## License

MIT
