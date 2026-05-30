# n8n Weekly Dev Summary Workflow (Bounty #5 — $200)

Automatically generate a **narrative weekly development summary** of any GitHub repository using the Claude API, delivered via email and Slack/Discord.

## What This Does

Every **Friday at 5pm** (configurable), this workflow:

1. **Fetches** commits, closed issues, and merged PRs from a GitHub repo for the current week
2. **Sends** the raw data to **Claude API** (`claude-sonnet-4-20250514`) for narrative summarization
3. **Delivers** the summary via:
   - 📧 **Email** (SMTP)
   - 💬 **Slack or Discord** (incoming webhook)

## Setup (3 Steps)

### Step 1: Import the Workflow

1. Open your n8n instance → **+ Add Workflow**
2. Click **...** (top right) → **Import from File**
3. Upload `workflow.json`
4. Click **Import**

### Step 2: Configure Environment Variables

Go to **Settings → Variables** and add:

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `REPO_OWNER` | ✅ | `facebook` | GitHub repo owner |
| `REPO_NAME` | ✅ | `react` | GitHub repo name |
| `ANTHROPIC_API_KEY` | ✅ | `sk-ant-...` | Your Anthropic API key |
| `SMTP_FROM` | 📧 | `noreply@company.com` | Email sender address |
| `SMTP_TO` | 📧 | `dev-team@company.com` | Recipient(s), comma-separated |
| `DESTINATION_WEBHOOK` | 💬 | `hooks.slack.com/...` | Slack/Discord webhook URL |
| `SUMMARY_LANGUAGE` | ❌ | `EN` or `FR` | Output language (default: EN) |

### Step 3: Configure Credentials

1. **GitHub PAT**: Create a credential of type **HTTP Basic Auth**:
   - Username: any value (ignored)
   - Password: your GitHub Personal Access Token (`repo` scope)

2. **SMTP**: Create an **SMTP** credential with your mail server details

3. **Activate** the workflow by clicking the toggle (top right)

## Architecture

```
┌─────────────┐
│  Cron Trigger │  (Friday 17:00)
└──────┬───────┘
       ▼
┌──────────────────┐
│ Compute Week Range │  (Monday→Sunday ISO dates)
└──┬──────┬───────┘
   ▼      ▼      ▼
┌──────┐ ┌──────┐ ┌──────────┐
│Commits│ │Issues│ │PRs       │  (GitHub API)
└──┬───┘ └──┬───┘ └────┬─────┘
   └────────┼────────┘
            ▼
   ┌────────────────┐
   │ Merge Data       │  (combine into prompt payload)
   └────────┬───────┘
            ▼
   ┌────────────────────┐
   │ Claude API           │  (generate narrative summary)
   └────────┬───────────┘
            ▼
   ┌──────────────────┐
   │ Parse Response     │  (extract text from Claude output)
   └──┬───────────┬───┘
      ▼           ▼
  ┌──────┐   ┌──────────┐
  │Slack │   │Email      │  (dual delivery)
  └──────┘   └──────────┘
```

## Customization

### Change Schedule
Edit the **Schedule Trigger** node → set `cronExpression` to your preferred schedule.

### Change Model
In the **Claude Narrative Summary** node, change the `model` parameter:
- `claude-sonnet-4-20250514` (default, balanced cost/quality)
- `claude-haiku-3-5-20241022` (faster, cheaper)
- `claude-opus-4-20250514` (best quality, most expensive)

### Add More Delivery Channels
Duplicate the **Post to Slack/Discord** node and change the URL for additional channels (e.g., Teams, Telegram).

## Requirements

- **n8n** v1.50+ (self-hosted or cloud)
- **Anthropic API key** (with billing enabled)
- **GitHub PAT** with `repo` scope (for private repos; public repos work without auth)
- **SMTP server** access (for email delivery; skip if only using webhooks)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Rate limit exceeded" on GitHub API | Add PAT credential (60 req/hr unauthenticated → 5000 authenticated) |
| Empty summary from Claude | Check `ANTHROPIC_API_KEY` is valid and has credits |
| Email not sending | Verify SMTP credentials in n8n Credentials panel |
| Webhook not firing | Ensure `DESTINATION_WEBHOOK` is set (node has `continueOnFail: true`) |

## Bounty Info

- **Bounty**: #5 ($200) from [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty)
- **Payment via**: Opire (automatic on merge)
- **Closes**: #2289
