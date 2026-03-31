# 📊 Weekly Dev Summary — n8n + Claude Workflow

An n8n workflow that automatically generates a weekly narrative summary of your GitHub repo's activity using the Claude API.

## What it does

Every Friday at 5 PM:
1. **Fetches** commits, closed issues, and merged PRs from the past 7 days
2. **Sends** the data to Claude (`claude-sonnet-4-20250514`) for narrative analysis
3. **Delivers** the summary to Discord and/or email

## Setup (5 steps)

### 1. Import the workflow
- Open n8n → **Workflows** → **Import from File**
- Select `weekly-dev-summary.json`

### 2. Set environment variables
In n8n → **Settings** → **Variables**:

| Variable | Required | Example |
|----------|----------|---------|
| `GITHUB_REPO` | ✅ | `facebook/react` |
| `CLAUDE_API_KEY` | ✅ | `sk-ant-api03-...` |
| `DISCORD_WEBHOOK_URL` | ✅* | `https://discord.com/api/webhooks/...` |
| `EMAIL_RECIPIENT` | ✅* | `team@example.com` |
| `SUMMARY_LANGUAGE` | ❌ | `EN` (default) or `FR` |

*At least one delivery method required.

### 3. Configure credentials

**GitHub Token** (for private repos or higher rate limits):
- n8n → **Credentials** → **New** → **Header Auth**
- Name: `GitHub Token`
- Header: `Authorization`
- Value: `token ghp_...`

**SMTP** (for email delivery):
- n8n → **Credentials** → **New** → **SMTP**
- Configure your mail server (Gmail, Resend, etc.)

### 4. Test
- Click **Execute Workflow** to run manually
- Check Discord/email for the summary

### 5. Activate
- Toggle the workflow **Active** — it will run every Friday at 5 PM (server time)

## Configuration

### Change the schedule
Edit the **Weekly Trigger** node's cron expression:
- `0 17 * * 5` = Friday 5 PM
- `0 9 * * 1` = Monday 9 AM
- `0 12 * * 3` = Wednesday noon

### Language
Set `SUMMARY_LANGUAGE` to `FR` for French summaries. The Claude prompt adapts automatically.

### Delivery
The workflow delivers to both Discord and email by default. To use only one:
- Remove the connection from **Format Output** to the unused delivery node
- Or delete the unused node entirely

## Workflow Architecture

```
┌──────────────┐
│  Cron Trigger │──┬── Fetch Commits ──┐
│  (Fri 5 PM)  │  ├── Fetch Issues  ──┼── Merge ── Aggregate ── Claude API ── Format ──┬── Discord
└──────────────┘  └── Fetch PRs    ──┘                                                  └── Email
```

## Sample Output

> ### 📊 Weekly Dev Summary — myorg/myapp (2026-03-28)
>
> **Overview:** This was a productive week with 23 commits across 4 contributors. The team focused on performance improvements and resolved several long-standing bugs in the authentication flow.
>
> **Key Changes:**
> - PR #142: Migrated session storage from JWT to database-backed tokens, improving security and enabling server-side revocation
> - PR #139: Reduced dashboard load time by 40% through query optimization and React Server Component adoption
> - Commit `a3f2b1c`: Added rate limiting to all public API endpoints
>
> **Bug Fixes:** Resolved 5 issues including the password reset race condition (#98) and timezone handling in recurring events (#103).
>
> **Contributors:** @alice (12 commits), @bob (8 commits), @carol (2 PRs), @dave (1 hotfix)
>
> **Looking Ahead:** Based on recent work, the team appears to be preparing for a major auth system overhaul. Expect more security-related changes next week.

## Requirements

- n8n 1.0+ (self-hosted or cloud)
- GitHub token (for private repos)
- Anthropic API key
- Discord webhook URL and/or SMTP credentials
