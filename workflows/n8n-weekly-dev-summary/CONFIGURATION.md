# Configuration Reference

All configuration is done via **n8n Variables** (Settings → Variables in your n8n instance).
No credentials are ever hardcoded in the workflow.

---

## Required Variables

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Repository to monitor in `owner/repo` format | `my-org/backend-api` |
| `GITHUB_TOKEN` | GitHub Personal Access Token — needs `repo` scope (read-only is fine) | `ghp_xxxxxxxxxxxx` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-xxxxxxxxxxxx` |

---

## Delivery Channel (pick one)

Set `DELIVERY_CHANNEL` to one of: `slack`, `discord`, or `email`

### Slack

| Variable | Description |
|---|---|
| `DELIVERY_CHANNEL` | `slack` |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL (create at api.slack.com/apps → Incoming Webhooks) |

### Discord

| Variable | Description |
|---|---|
| `DELIVERY_CHANNEL` | `discord` |
| `DISCORD_WEBHOOK_URL` | Discord channel webhook URL (channel Settings → Integrations → Webhooks) |

### Email (SMTP)

| Variable | Description | Example |
|---|---|---|
| `DELIVERY_CHANNEL` | `email` | |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (587 for TLS, 465 for SSL) | `587` |
| `SMTP_USER` | SMTP username / sender address | `bot@yourcompany.com` |
| `SMTP_PASS` | SMTP password or app password | `••••••••` |
| `SMTP_TO` | Recipient email address(es) | `team@yourcompany.com` |

**Gmail tip:** Use an [App Password](https://myaccount.google.com/apppasswords) rather than your main password if you have 2FA enabled.

---

## Optional Variables

| Variable | Default | Description |
|---|---|---|
| `SUMMARY_LANGUAGE` | `EN` | Language for the narrative — `EN` (English) or `FR` (French) |

---

## Schedule

The workflow triggers every **Friday at 17:00 UTC** by default.

To change the schedule, open the **"Every Friday at 5 PM"** node and edit the cron expression:

| Cron | Meaning |
|---|---|
| `0 17 * * 5` | Friday 17:00 UTC (default) |
| `0 9 * * 1` | Monday 09:00 UTC |
| `0 8 * * 1-5` | Weekdays at 08:00 UTC |

---

## GitHub Token Permissions

The token only needs **read access**. When creating the token at github.com/settings/tokens:

- For classic tokens: check `repo` (or just `public_repo` for public repositories)
- For fine-grained tokens: grant `Contents: Read` and `Issues: Read` on the target repository
