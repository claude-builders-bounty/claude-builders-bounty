# Weekly Dev Summary — n8n Workflow

Automated weekly narrative summary of GitHub repo activity, powered by Claude API and delivered via Discord/Slack.

## What It Does

1. **Cron trigger** — Fires every Friday at 5:00 PM
2. **Fetches GitHub data** — commits, closed issues, merged PRs for the past week
3. **Claude summarization** — generates a structured narrative summary
4. **Delivery** — sends to Discord webhook (or Slack)

## Setup (5 Steps)

### 1. Import the Workflow

- Open n8n → Click **"Import from File"**
- Select `workflow.json`

### 2. Configure GitHub Credentials

Create a **GitHub Personal Access Token** with `repo` scope:

```
Settings → Developer settings → Personal access tokens → Generate new token
```

In n8n:
- **Credentials** → Add **Header Auth**
- **Name:** `GitHub API`
- **Value:** `Bearer YOUR_GITHUB_TOKEN`

### 3. Configure Claude API

In n8n:
- **Credentials** → Add **OpenAI API** (Claude uses OpenAI-compatible API)
- **API Key:** `YOUR_CLAUDE_API_KEY`
- **Base URL:** `https://api.anthropic.com/v1`

> Note: Use the `claude-sonnet-4-20250514` model or latest available.

### 4. Set Variables

In n8n **Variables** panel, add:

| Variable | Example |
|----------|---------|
| `REPO` | `owner/project-name` |
| `WEEK_START` | `2026-03-20` |
| `WEEK_END` | `2026-03-27` |
| `DISCORD_WEBHOOK_ID` | `123456789` |
| `DISCORD_WEBHOOK_NAME` | `dev-summary` |
| `GITHUB_API_URL` | `https://api.github.com` |

Or hardcode in the node parameters by replacing the variable references.

### 5. Activate

- Toggle workflow **Active**
- Click **Test** to verify execution

## Sample Output

```markdown
## Weekly Dev Summary — MyProject

**Period:** 2026-03-20 → 2026-03-27

### Added
- #42: New user authentication flow

### Fixed
- #38: Login redirect loop on mobile

### Changed
- Refactored database connection pooling

### Removed
- Deprecated /api/v1/users endpoint
```

## Discord/Slack Alternative

To use **Slack** instead of Discord, replace the final node with:

- Node type: `n8n-nodes-base.slack`
- Operation: `Send Message`
- Webhook URL: from your Slack App

## Cron Expression

The default cron is `0 17 * * 5` (Friday 5pm). To change:

1. Edit the **Cron Trigger** node
2. Update the cron expression
3. Save and reactivate

## Troubleshooting

- **No data returned:** Verify your `REPO` variable matches `owner/repo-name`
- **Claude errors:** Check API key and model availability
- **Discord fails:** Ensure webhook has permission to post in the channel
