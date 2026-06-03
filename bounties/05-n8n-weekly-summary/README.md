# Weekly GitHub Dev Summary — n8n Workflow

Complete n8n workflow that generates a weekly narrative summary of a GitHub repository's activity using the Claude API.

## What it does

Every week (configurable cron), this workflow:
1. Fetches the last 7 days of **commits, closed issues, and merged PRs** from any GitHub repo
2. Builds a structured prompt
3. Calls **Claude Sonnet 4** (`claude-sonnet-4-20250514`) to generate a 3-5 paragraph narrative summary
4. Sends the summary to **Discord** (webhook) and/or **Email**

## Files

- `weekly-github-summary.json` — importable n8n workflow (10 KB)
- `README.md` — this file

## Setup (5 steps)

### 1. Import the workflow in n8n

- Open n8n → Workflows → Import from File
- Select `weekly-github-summary.json`

### 2. Configure credentials in n8n

- **GitHub API:** Settings → Credentials → New → GitHub API
  - Use a Personal Access Token (PAT) with `repo` and `read:org` scopes
- **Anthropic API:** Set environment variable `ANTHROPIC_API_KEY`

### 3. Set environment variables

```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional (with defaults)
export GITHUB_OWNER="claude-builders-bounty"
export GITHUB_REPO="claude-builders-bounty"
export SUMMARY_LANGUAGE="English"

# Delivery (pick one or both)
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export EMAIL_FROM="noreply@yourdomain.com"
export EMAIL_TO="team@yourdomain.com"
```

### 4. Activate the workflow

Click the toggle in n8n to activate. The default schedule is every 168 hours (1 week).

To change to "Friday 5pm" specifically, edit the Schedule Trigger node:
- Mode: Cron
- Expression: `0 17 * * 5`

### 5. Test execution

Click "Execute Workflow" to run it once. The summary will be sent to Discord/Email.

## Configurable Variables

| Variable | Default | Description |
|---|---|---|
| `github_owner` | `claude-builders-bounty` | GitHub org/user |
| `github_repo` | `claude-builders-bounty` | Repo name |
| `summary_language` | `English` | Output language (English, French, Spanish, etc.) |
| `days_back` | `7` | How many days of history to include |
| `discord_webhook_url` | (none) | Discord webhook for delivery |
| `email_from` / `email_to` | (none) | Email delivery (alternative) |

## Sample Output

```
📊 Weekly Dev Summary — claude-builders-bounty/claude-builders-bounty

This was a productive week for the project with 28 commits, 12 issues closed,
and 5 PRs merged. The most significant work involved adding a new pre-tool-use
security hook that blocks destructive bash commands, and a comprehensive PR
review agent that uses regex pattern matching to identify common security risks
in submitted code.

Highlights:
- 🛡️ Pre-tool-use security hook (PR #2434) — blocks rm -rf, DROP TABLE, etc.
- 🤖 PR review agent (PR #2435) — analyzes diffs for 10+ risk patterns
- 📚 CHANGELOG generator (PR #2437) — auto-categorizes commits

---
*Generated 2026-06-03T19:30:00Z | 28 commits, 12 issues closed, 5 PRs merged*
```

## Acceptance Criteria (from issue #5)

- [x] Exportable n8n workflow (importable `.json` file)
- [x] Trigger: weekly cron (configurable, default 168h)
- [x] Fetches from GitHub API: commits, closed issues, merged PRs
- [x] Calls Claude API (`claude-sonnet-4-20250514`)
- [x] Delivers via Discord webhook AND Email (both options, documented)
- [x] Configurable: GitHub repo, language, delivery channel
- [x] Tested workflow JSON (validated against n8n schema)
- [x] README with setup in 5 steps

## Tested

- ✅ JSON is valid n8n workflow format
- ✅ All node types are n8n-nodes-base (built-in, no custom nodes)
- ✅ Workflow connections are valid (all nodes connected)
- ✅ HTTP request URLs use placeholder env vars
- ✅ Code nodes use sandboxed JS (no dangerous operations)

## License

MIT
