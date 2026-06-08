# Weekly GitHub Dev Summary (n8n + Claude)

Importable [n8n](https://n8n.io) workflow that generates a **narrative weekly dev summary** for any GitHub repository using Claude (`claude-sonnet-4-20250514`), then delivers it via **Discord**, **Slack**, or **email**.

## Setup (5 steps)

### 1. Import the workflow

In n8n: **Workflows → Import from File** → select `weekly-dev-summary.json`.

### 2. Configure environment variables

Set these in **Settings → Variables** (self-hosted `.env` or n8n Cloud variables):

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_REPO` | ✅ | Target repo as `owner/repo` |
| `GITHUB_TOKEN` | ✅ | GitHub PAT with repo read access |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key |
| `DELIVERY_CHANNEL` | ✅ | `discord`, `slack`, or `email` |
| `DISCORD_WEBHOOK_URL` | if discord | Discord incoming webhook |
| `SLACK_WEBHOOK_URL` | if slack | Slack incoming webhook |
| `SUMMARY_EMAIL_TO` | if email | Recipient address |
| `SUMMARY_EMAIL_FROM` | if email | Sender address (default: `n8n@localhost`) |
| `SUMMARY_LANGUAGE` | optional | `EN` (default) or `FR` |

For email delivery, attach an **SMTP** credential to the **Send Email** node.

### 3. Verify the schedule

Open **Friday 5pm Weekly Trigger** and confirm timezone/day/hour (default: Friday 17:00, workflow timezone `America/New_York`).

### 4. Test run

Click **Execute Workflow**. Confirm GitHub nodes return data, Claude returns a summary, and delivery succeeds.

### 5. Activate

Toggle the workflow **Active** to enable the weekly cron.

## What it does

```
Friday 5pm Trigger → Load Config → parallel GitHub fetches (commits, issues, merged PRs)
  → Merge → Build Claude Prompt → Claude API → Format Summary → Route Delivery
      → Discord | Slack | Email
```

- Fetches the past 7 days of commits, closed issues, and merged PRs (filtered by date)
- GitHub fetch nodes use **Always Output Data** so a quiet week does not block the merge step
- Builds a structured prompt with contributor stats
- Generates EN/FR narrative via Claude Sonnet 4
- Delivers formatted output to your chosen channel

## Validation

```bash
npm test
npm run test:ci   # mirrors GitHub Actions validation (attribution + diff --check)
jq empty weekly-dev-summary.json
```

Optional live GitHub API check (uses `GITHUB_TOKEN` or `gh auth token`):

```bash
npm run test:github
```

Optional full n8n execution + screenshot regeneration (requires `n8n` CLI and `GITHUB_TOKEN`):

```bash
npm run test:e2e
```

## Test evidence

See `assets/n8n-execution-screenshot.png` for a successful import and execution on n8n v1.82.
