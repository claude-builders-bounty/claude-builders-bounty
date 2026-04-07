# n8n Weekly Dev Summary Workflow

Automated weekly narrative summary of a GitHub repository's activity,
powered by the Claude API (`claude-sonnet-4-20250514`).

Closes #5.

## What It Does

Every Friday at 5 pm (configurable), the workflow:

1. Fetches the last 7 days of **commits**, **closed issues**, and **merged PRs**
   from the GitHub API.
2. Sends the raw data to the **Claude API**, which generates a themed narrative
   summary (not a bullet dump).
3. Delivers the summary to **Discord** (webhook) or **Email** (SMTP) --
   your choice.

## Setup (5 Steps)

### 1. Import the workflow

Open your n8n instance, go to **Workflows > Import from File**, and select
`n8n-weekly-dev-summary.json`.

### 2. Create credentials

| Credential name | Type | Value |
|---|---|---|
| `GitHub Token` | Header Auth | `Authorization: token <GITHUB_PAT>` |
| `Anthropic API Key` | Header Auth | `x-api-key: <ANTHROPIC_API_KEY>` |
| `SMTP` *(email only)* | SMTP | Your SMTP server details |

> **Tip:** For `Header Auth`, set the header name and value exactly as shown.
> The GitHub PAT needs `repo` scope (or `public_repo` for public repos).

### 3. Set environment variables

In **Settings > Environment Variables** (or your `.env` / Docker config):

| Variable | Required | Default | Example |
|---|---|---|---|
| `GITHUB_REPO` | Yes | `n8n-io/n8n` | `owner/repo` |
| `SUMMARY_LANGUAGE` | No | `EN` | `EN` or `FR` |
| `DELIVERY_CHANNEL` | No | `discord` | `discord` or `email` |
| `DISCORD_WEBHOOK_URL` | If discord | -- | `https://discord.com/api/webhooks/...` |
| `EMAIL_FROM` | If email | `n8n@example.com` | `team@company.com` |
| `EMAIL_TO` | If email | -- | `dev-team@company.com` |

### 4. Test

Click the **Manual Test Trigger** node, then **Execute Workflow**.
Verify you receive the summary in your chosen channel.

### 5. Activate

Toggle the workflow **Active**. The cron trigger fires every Friday at 17:00
server time.

## Workflow Architecture

```
                           +-------------------+
                           | Cron: Fri 5pm     |
   +-----------------+     | (or Manual Test)  |
   |   Set Config    |<----+-------------------+
   | (repo, lang,    |
   |  delivery)      |
   +--------+--------+
            |
   +--------+--------+--------+
   |                 |         |
   v                 v         v
Fetch Commits   Fetch Issues  Fetch PRs
   (7 days)      (closed)     (merged)
   |                 |         |
   +--------+--------+--------+
            |
            v
   +-------------------+
   | Aggregate Data    |
   | (normalize JSON)  |
   +--------+----------+
            |
            v
   +-------------------+
   | Claude API        |
   | (narrative gen)   |
   +--------+----------+
            |
            v
   +-------------------+
   | Format Output     |
   +--------+----------+
            |
            v
   +-------------------+
   | Route: Discord    |
   |   or Email?       |
   +--------+----------+
        |         |
        v         v
   Discord     Email
   Webhook     (SMTP)
```

## Features

- **Parallel GitHub API fetches** -- commits, issues, and PRs are fetched
  concurrently for speed.
- **Narrative summaries** -- Claude groups related changes into themes instead
  of dumping raw lists.
- **Bilingual** -- set `SUMMARY_LANGUAGE=FR` for French summaries.
- **Dual delivery** -- Discord webhook embed or plain-text email.
- **Manual trigger** -- test anytime without waiting for cron.
- **Configurable via env vars** -- no need to edit the workflow JSON.

## Sample Output

See [SAMPLE_OUTPUT.md](./SAMPLE_OUTPUT.md) for an example of the generated summary.

## Troubleshooting

| Symptom | Fix |
|---|---|
| 401 on GitHub API | Check PAT has `repo` scope and Header Auth is `Authorization: token <PAT>` |
| 401 on Claude API | Check Header Auth is `x-api-key: <KEY>` and `anthropic-version` header is present |
| Empty summary | Repo may have had no activity in the past 7 days -- this is reported gracefully |
| Discord 400 | Embed description is capped at 4000 chars; very active repos may hit this |
