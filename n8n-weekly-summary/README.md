# 📊 Weekly GitHub Dev Summary — n8n + Claude AI

Automated n8n workflow that generates a weekly narrative summary of a GitHub repository's activity using Claude AI, delivered via Discord or Slack webhook.

## What it does

Every Friday at 5pm, the workflow:

1. 📥 **Fetches** the past 7 days of GitHub activity (commits, closed issues, merged PRs)
2. 🔄 **Merges** all data into a structured payload
3. 🤖 **Sends** to Claude (`claude-sonnet-4-20250514`) for narrative summary generation
4. 📤 **Delivers** the formatted summary via Discord or Slack webhook

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌─────────────┐     ┌──────────────┐
│  Cron Trigger│ ──► │ GitHub API   │ ──► │ Merge + Code  │ ──► │ Claude API  │ ──► │ Discord/Slack│
│  (Fri 5pm)  │     │ (3 parallel) │     │   Node        │     │ (narrative) │     │  Webhook     │
└─────────────┘     └──────────────┘     └───────────────┘     └─────────────┘     └──────────────┘
```

## Setup (5 steps)

### 1. Import the workflow

In n8n: **Workflows → Import from File → select `workflow.json`**

### 2. Configure GitHub credentials

Go to **Credentials → Add Credential → GitHub API** and add your Personal Access Token.

### 3. Set n8n variables

Go to **Settings → Variables** and add:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Target repository (owner/repo) | `facebook/react` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-...` |
| `WEBHOOK_URL` | Discord or Slack webhook URL | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Summary language | `EN` or `FR` |

### 4. Test the workflow

Click **Execute Workflow** (▶) to run a manual test. Verify the summary appears in your Discord/Slack channel.

### 5. Activate

Toggle the workflow to **Active** (green). It will now run automatically every Friday at 5pm.

## Output example

The generated summary looks like this in Discord:

```markdown
📊 Weekly Dev Summary: facebook/react (2026-03-21 to 2026-03-28)

## Highlights
A productive week for the React team! The focus was on improving Server
Components performance and squashing bugs in the reconciler.

## What Shipped
- **Server Components Streaming** — PR #32455 by @sebmarkbage landed a
  major optimization for streaming SSR, reducing TTFB by ~200ms.
- **useActionState improvements** — PR #32460 added better error
  boundaries for server actions.

## Bug Fixes & Maintenance
- Fixed a memory leak in the fiber scheduler (#32470)
- Updated TypeScript definitions for React 19.1 (#32468)
- Cleaned up legacy createRoot warnings (#32465)

## Community Activity
- 12 issues closed, 8 new issues opened
- 3 first-time contributors merged PRs 🎉

## What's Next
Based on open PRs, expect improvements to the React DevTools
and continued work on the compiler optimization pipeline.

> "Ship early, ship often, and listen to your users." — Reid Hoffman
```

## Customization

### Change the schedule

Edit the **Schedule Trigger** node to adjust timing (e.g., Monday 9am, daily, etc.)

### Change the delivery method

Replace the final **Send to Discord/Slack** node with:
- **Email (SMTP):** Use the n8n Email node
- **Telegram:** Use the Telegram node
- **Custom API:** HTTP Request to any endpoint

### Change the AI model

Edit the **Generate Summary (Claude)** node and change the `model` field to any Anthropic model (e.g., `claude-3-5-haiku-20241022` for faster/cheaper summaries).

## Architecture

| Node | Type | Purpose |
|------|------|---------|
| Weekly Trigger | Schedule Trigger | Fires every Friday at 5pm |
| Fetch Commits | HTTP Request | `GET /repos/{owner}/{repo}/commits?since=7d` |
| Fetch Closed Issues | HTTP Request | `GET /repos/{owner}/{repo}/issues?state=closed&since=7d` |
| Fetch Merged PRs | HTTP Request | `GET /repos/{owner}/{repo}/pulls?state=closed` |
| Merge GitHub Data | Code | Structures + filters data, separates PRs from issues |
| Generate Summary | HTTP Request | `POST api.anthropic.com/v1/messages` |
| Format Output | Code | Extracts text, builds delivery payload |
| Send to Discord/Slack | HTTP Request | `POST webhook_url` with embed |

## Requirements

- n8n (self-hosted or cloud)
- GitHub Personal Access Token (for API)
- Anthropic API key
- Discord or Slack webhook URL

## License

MIT
