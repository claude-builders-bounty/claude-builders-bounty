# Weekly Dev Summary — n8n + Claude API

An n8n workflow that automatically generates a **narrative weekly development summary** for any GitHub repository, powered by the Claude API (`claude-sonnet-4-20250514`).

> **Bounty Issue**: [#5 — n8n + Claude Code weekly dev summary](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

---

## What It Does

Every **Friday at 5:00 PM** (configurable), the workflow:

1. **Fetches** the past week's commits, closed issues, and merged PRs from the GitHub API
2. **Aggregates** the data (counts, top contributors, key messages)
3. **Calls Claude** (`claude-sonnet-4-20250514`) to generate a structured Markdown narrative summary
4. **Delivers** the summary to:
   - 📄 **Markdown file** (saved to configurable directory)
   - 💬 **Slack** (if webhook URL configured)
   - 🎮 **Discord** (if webhook URL configured)
   - 📋 **n8n execution log** (always available)

### Sample Output

> **Weekly Dev Summary — your-org/your-repo**
> _2026-05-26 → 2026-06-02_
>
> ### Overview
> This was a productive week with 23 commits across 6 contributors...
>
> ### By the Numbers
> - Commits: 23 | PRs Merged: 5 | Issues Closed: 8
>
> ### Top Contributors
> - alice (9 commits), bob (7 commits)...
>
> ### Key Changes
> - Refactored auth module (#142)
> - Added rate limiting to API (#145)
>
> ### Closed Issues
> - #138 Memory leak in worker pool
> - #140 Dashboard loading time
>
> ### Looking Ahead
> Keep up the momentum! 🚀

---

## Files Included

| File | Description |
|---|---|
| `weekly-dev-summary.json` | Importable n8n workflow JSON |
| `weekly_dev_summary.py` | Python standalone script alternative |
| `contributor_meta.json` | Contributor metadata and feature manifest |
| `README.md` | This documentation |

---

## Setup — n8n Workflow (5 Steps)

### Step 1 — Import the Workflow

In your n8n instance, go to **Workflows → Import from File** and upload `weekly-dev-summary.json`.

### Step 2 — Create GitHub API Credential

1. Go to **Credentials → New Credential → Header Auth**
2. Name it `GitHub API Token`
3. Set **Header Name** to `Authorization`
4. Set **Header Value** to `Bearer ghp_YOUR_GITHUB_TOKEN` (use a [personal access token](https://github.com/settings/tokens) with `repo` scope)
5. In the workflow, edit each **Fetch** node (Fetch Commits, Fetch Closed Issues, Fetch Merged PRs) → select this credential

### Step 3 — Create Claude API Credential

1. Go to **Credentials → New Credential → Header Auth**
2. Name it `Claude API Key`
3. Set **Header Name** to `x-api-key`
4. Set **Header Value** to your [Anthropic API key](https://console.anthropic.com/)
5. In the **Generate Summary (Claude)** node → select this credential

> ⚠️ The Claude API request also requires custom headers. Open the **Generate Summary (Claude)** node → **Headers** section and verify:
> - `anthropic-version` → `2023-06-01`
> - `content-type` → `application/json`

### Step 4 — Configure Variables

Edit the **Config** node and set:

| Variable | Description | Default | Example |
|---|---|---|---|
| `githubOwner` | GitHub org or user | `claude-builders-bounty` | `your-org` |
| `githubRepo` | Repository name | `claude-builders-bounty` | `your-repo` |
| `language` | Output language (`EN` or `FR`) | `EN` | `FR` |
| `slackWebhookUrl` | Slack incoming webhook URL | _(empty)_ | `https://hooks.slack.com/...` |
| `discordWebhookUrl` | Discord webhook URL | _(empty)_ | `https://discord.com/api/webhooks/...` |
| `outputDir` | Directory for Markdown output | `/tmp/weekly-dev-summary` | `/home/user/summaries` |

All variables can also be set via environment variables:

| Env Variable | Config Field |
|---|---|
| `GITHUB_OWNER` | `githubOwner` |
| `GITHUB_REPO` | `githubRepo` |
| `SUMMARY_LANGUAGE` | `language` |
| `SLACK_WEBHOOK_URL` | `slackWebhookUrl` |
| `DISCORD_WEBHOOK_URL` | `discordWebhookUrl` |
| `OUTPUT_DIR` | `outputDir` |

### Step 5 — Activate & Test

1. Click **Active** to enable the scheduled trigger
2. Click **Test Workflow** to run it manually and verify output
3. Check the output nodes:
   - **Save Markdown File** — verify the `.md` file is created
   - **Post to Slack** / **Post to Discord** — check your channel
   - **Log Summary** — view in n8n execution history

---

## Setup — Python Script (Alternative)

If you prefer not to use n8n, a standalone Python script is included.

### Prerequisites

- Python 3.10+
- `requests` library (`pip install requests`)

### Quick Start

```bash
# Set required environment variables
export GITHUB_TOKEN="ghp_YOUR_GITHUB_TOKEN"
export ANTHROPIC_API_KEY="sk-ant-YOUR_API_KEY"

# Run with defaults
python weekly_dev_summary.py --owner your-org --repo your-repo

# With all options
python weekly_dev_summary.py \
  --owner your-org \
  --repo your-repo \
  --language FR \
  --slack-url "https://hooks.slack.com/services/..." \
  --discord-url "https://discord.com/api/webhooks/..." \
  --output-dir ./summaries \
  --days 7
```

### CLI Options

| Option | Description | Default |
|---|---|---|
| `--owner` | GitHub repository owner (required) | — |
| `--repo` | GitHub repository name (required) | — |
| `--language` | Output language: `EN` or `FR` | `EN` |
| `--slack-url` | Slack webhook URL | From `SLACK_WEBHOOK_URL` env |
| `--discord-url` | Discord webhook URL | From `DISCORD_WEBHOOK_URL` env |
| `--output-dir` | Directory for Markdown output | `/tmp/weekly-dev-summary` |
| `--days` | Number of days to look back | `7` |

### Cron Setup (Linux/macOS)

```bash
# Run every Friday at 5pm
0 17 * * 5 cd /path/to/script && python weekly_dev_summary.py --owner your-org --repo your-repo >> /var/log/weekly-summary.log 2>&1
```

---

## Architecture

```
Schedule (Fri 5pm cron)
  → Config (repo, language, webhooks, output dir)
    → Compute Date Range (last 7 days)
      → Fetch Commits ──────────┐
      → Fetch Closed Issues ────┤→ Aggregate Data → Claude API → Extract Summary
      → Fetch Merged PRs ───────┘        │
                                          ├──→ Save Markdown File
                                          ├──→ Has Slack? → Post to Slack
                                          ├──→ Has Discord? → Post to Discord
                                          └──→ Log Summary
```

---

## Delivery Options

| Method | How | Status |
|---|---|---|
| **Markdown File** | Saved to `outputDir` with date-range filename | ✅ Always |
| **Slack** | Set `slackWebhookUrl` in Config node or env | 🔧 Optional |
| **Discord** | Set `discordWebhookUrl` in Config node or env | 🔧 Optional |
| **Email** | Replace Log Summary node with n8n's Send Email node | 🔧 Optional |
| **n8n Log** | View in execution history | ✅ Always |

---

## Customizing the Cron Schedule

To change the trigger time, edit the **Weekly Trigger** node's cron expression:

| Schedule | Cron Expression |
|---|---|
| Friday 5:00 PM | `0 17 * * 5` |
| Monday 9:00 AM | `0 9 * * 1` |
| Every day at midnight | `0 0 * * *` |
| First of each month | `0 0 1 * *` |

---

## Requirements

| Component | Version | Notes |
|---|---|---|
| **n8n** | 1.0+ | Self-hosted or cloud |
| **GitHub** | API v3 | Personal access token with `repo` scope |
| **Anthropic** | Messages API | API key with access to `claude-sonnet-4-20250514` |
| **Slack** | Incoming Webhooks | Optional |
| **Discord** | Webhooks | Optional |

---

## Troubleshooting

| Issue | Fix |
|---|---|
| GitHub returns 401 | Check token has `repo` scope, header is `Bearer ghp_...` |
| Claude returns 401 | Verify `x-api-key` header and `anthropic-version: 2023-06-01` |
| Empty commits/issues | Ensure the repo had activity in the past week; check date range |
| Slack not receiving | Test webhook: `curl -X POST -H 'Content-type: application/json' --data '{"text":"test"}' YOUR_URL` |
| Discord not receiving | Same as Slack; ensure URL format: `https://discord.com/api/webhooks/...` |
| Python script fails | Check `GITHUB_TOKEN` and `ANTHROPIC_API_KEY` env vars are set |
| Markdown file not saved | Verify `outputDir` exists and is writable |

---

## Testing

### n8n Workflow
1. Import the JSON file
2. Set up credentials (Steps 2-3 above)
3. Click **Test Workflow** to run manually
4. Verify output in the Save Markdown File node and notification channels

### Python Script
```bash
# Quick test with a public repo
GITHUB_TOKEN="ghp_YOUR_TOKEN" ANTHROPIC_API_KEY="sk-ant-YOUR_KEY" \
  python weekly_dev_summary.py --owner claude-builders-bounty --repo claude-builders-bounty
```

---

## License

MIT — same as the parent repository.
