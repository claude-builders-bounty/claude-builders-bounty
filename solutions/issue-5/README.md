# n8n Workflow: Weekly GitHub Summary with Claude

Automated weekly development summary generator using n8n + Claude API.

## Quick Start (5 Steps)

### 1. Import Workflow

```bash
# In n8n, go to Workflows > Import from File
# Select: weekly-github-summary.json
```


### 2. Configure Credentials

Add these credentials in n8n (Settings > Credentials):

- **GitHub API**: Personal access token with `repo` scope
- **Anthropic API**: API key from console.anthropic.com
- **SMTP** (optional): Email server for notifications
- **Discord Webhook** (optional): Webhook URL from channel settings

### 3. Set Environment Variables

Create/update `.env` file:

```bash
GITHUB_REPO=owner/repo-name
LANGUAGE=EN  # EN or FR
DISCORD_WEBHOOK=https://discord.com/api/webhooks/.../...  # optional
EMAIL_TO=team@example.com  # optional
```


### 4. Configure Delivery Method

Edit workflow nodes:

- **Email only**: Delete "Discord" node
- **Discord only**: Delete "Send Email" node
- **Both**: Keep both nodes (default)

### 5. Activate Workflow

- Click "Active" toggle in n8n
- Workflow runs every Friday at 5 PM

---

## Features

✅ **Automated Weekly Trigger** - Every Friday at 5 PM
✅ **GitHub Activity Collection**:
  - Commits from past 7 days
  - Closed issues
  - Merged pull requests
✅ **Claude-Powered Summaries** - Professional narrative reports
✅ **Multiple Delivery Channels**:
  - Email (via SMTP)
  - Discord webhook
  - Slack webhook (easy to add)
✅ **Configurable**:
  - GitHub repository
  - Output language (EN/FR)
  - Delivery channels
✅ **Production Ready** - Tested on real n8n instance

---

## Workflow Overview

```
┌─────────────┐
│   Weekly    │
│   Trigger   │ (Friday 5PM)
└──────┬──────┘
       │
       ├────────────────────────────┐
       │                            │
       ▼                            ▼
┌─────────────┐            ┌─────────────┐
│     Get     │            │     Get     │
│   Commits   │            │   Issues    │
└──────┬──────┘            └──────┬──────┘
       │                            │
       └────────────┬───────────────┘
                    │
                    ▼
             ┌─────────────┐
             │     Get     │
             │     PRs     │
             └──────┬──────┘
                    │
                    ▼
             ┌─────────────┐
             │   Process   │
             │    Data     │
             └──────┬──────┘
                    │
                    ▼
             ┌─────────────┐
             │   Claude    │
             │    API      │
             └──────┬──────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   ┌─────────────┐    ┌─────────────┐
   │    Send     │    │   Discord   │
   │    Email    │    │  Webhook    │
   └─────────────┘    └─────────────┘
```

---

## Sample Output

**Subject:** Weekly Dev Summary - owner/repo - 2026-03-27

**Body:**

# Weekly Development Summary
**Repository:** owner/repo
**Period:** 2026-03-20 to 2026-03-27

## Overview

This week saw significant progress on the authentication system with 23 commits, 8 closed issues, and 3 merged pull requests.

## Key Commits

1. **Implement OAuth2 flow** (abc123) by Alice
2. **Add rate limiting** (def456) by Bob
3. **Fix CSRF vulnerability** (ghi789) by Charlie

## Closed Issues

- #45: User authentication timeout
- #46: Session management bug
- #47: Password reset flow

## Merged Pull Requests

- #50: OAuth2 implementation (by Alice)
- #51: Rate limiting middleware (by Bob)
- #52: Security patches (by Charlie)

## Contributors

Special thanks to: Alice (12 commits), Bob (8 commits), Charlie (3 commits)

## Recommendations

1. Continue security audit next week
2. Performance testing on new auth flow
3. Update documentation

---

## Configuration Options

### Language Selection

Set `LANGUAGE` environment variable:

```bash
LANGUAGE=EN  # English (default)
LANGUAGE=FR  # French
```


### Custom Schedule

Edit the Cron expression in "Weekly Trigger" node:

```bash
0 17 * * 5  # Friday 5 PM (default)
0 9 * * 1   # Monday 9 AM
0 12 * * *  # Daily at noon
```


### Custom Prompt

Edit the Claude API node's message content to customize the summary format.

---

## Requirements

- n8n (version 1.0+)
- GitHub Personal Access Token
- Anthropic API Key
- SMTP server (for email) OR Discord webhook

---

## Testing

### Manual Test

1. Open workflow in n8n
2. Click "Execute Workflow"
3. Check output in each node

### Expected Output

- Process Data node: JSON with stats
- Claude API node: Narrative summary
- Email/Discord node: Success confirmation

---

## Troubleshooting

**GitHub API errors:**
- Check token has `repo` scope
- Verify repository exists and is accessible

**Claude API errors:**
- Verify API key is valid
- Check usage limits at console.anthropic.com

**Email not sending:**
- Verify SMTP credentials
- Check spam folder

**Discord not receiving:**
- Verify webhook URL
- Check channel permissions

---

## Cost Estimate

- **GitHub API**: Free (within rate limits)
- **Claude API**: ~$0.01 per summary (Sonnet)
- **n8n**: Free (self-hosted) or ~$20/month (cloud)

---

## License

MIT

---

## Author

disillusi0n - Created for claude-builders-bounty Issue #5

**Bounty:** $200
