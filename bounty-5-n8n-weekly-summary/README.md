# Weekly Dev Summary — n8n + Claude Workflow

> Bounty #5 ($200): Complete n8n workflow that generates a weekly narrative summary of GitHub repo activity using Claude API.

## Quick Setup (5 Steps)

### Step 1: Import the Workflow

1. Open your n8n instance
2. Click **"..."** → **Import from File**
3. Upload `weekly-dev-summary.json`

### Step 2: Configure Credentials

In n8n, go to **Settings → Credentials** and add:

| Credential | Type | Value |
|------------|------|-------|
| GitHub Token | HTTP Header Auth | `Authorization: Bearer ghp_YOUR_TOKEN` |
| Anthropic API | Anthropic API | Your API key from console.anthropic.com |
| SMTP (optional) | SMTP | Your email server settings |

### Step 3: Configure Variables

In the workflow, go to **Settings → Variables** and update:

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_REPO` | GitHub repo in `owner/repo` format | `owner/repo` |
| `GITHUB_API` | GitHub API base URL | `https://api.github.com` |
| `LANGUAGE` | Summary language (`EN` or `FR`) | `EN` |
| `WEBHOOK_URL` | Discord or Slack webhook URL | (your webhook) |
| `EMAIL_TO` | Email recipient (optional) | `team@yourdomain.com` |

### Step 4: Enable the Workflow

Click the **Active** toggle in n8n to enable the scheduled trigger.

### Step 5: Test

Click **"Test Workflow"** to run it manually and verify the output.

## What It Does

Every **Friday at 5pm**, the workflow:

1. **Fetches** from GitHub API:
   - Commits from the past 7 days
   - Issues closed this week
   - Pull requests merged this week

2. **Processes** the data:
   - Counts commits, contributors, merged PRs, closed issues
   - Formats titles and links

3. **Generates** a narrative summary via Claude (`claude-sonnet-4-20250514`):
   - 📊 By the Numbers
   - 🚀 Highlights (2-3 most impactful changes)
   - 📋 Merged Pull Requests
   - ✅ Closed Issues
   - 👏 Contributors

4. **Delivers** the summary via:
   - Discord/Slack webhook (primary)
   - Email (secondary, optional)

## Delivery Options

### Discord Webhook

```env
WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdef...
```

### Slack Webhook

```env
WEBHOOK_URL=https://hooks.slack.com/services/T000/B000/XXX
```

### Email Only

Disable the "Send to Discord/Slack" node and configure the "Send via Email" node with your SMTP credentials.

## Configuration Options

| Option | Description | Values |
|--------|-------------|--------|
| Schedule day | Which day to run | Edit the Schedule Trigger node |
| Schedule time | What time to run | Edit the Schedule Trigger node (default: 17:00) |
| Language | Summary language | `EN` (English) or `FR` (French) |
| Repo | Target repository | Any public GitHub repo, or private with token |
| Delivery | Output channels | Discord, Slack, or email (enable/disable nodes) |

## Output Example

```markdown
## Weekly Dev Summary — my-org/my-project
### 📊 By the Numbers
- 23 commits by 5 contributors
- 7 merged PRs, 4 closed issues

### 🚀 Highlights
- **New authentication system** — Replaced session-based auth with JWT tokens (#142)
- **Performance optimization** — Reduced API response time by 40% through query caching (#138)
- **Mobile responsive dashboard** — All pages now work on tablets and phones (#145)

### 📋 Merged Pull Requests
- [#147] Fix race condition in payment processing (by @alice)
- [#146] Add rate limiting to public endpoints (by @bob)
...

### ✅ Closed Issues
- [#140] API returns 500 on empty search queries
...

### 👏 Contributors
Thanks to @alice, @bob, @charlie, @diana, and @eve for their contributions this week!
```

## Screenshot

*(See `screenshot.png` for a screenshot of successful execution in n8n)*

## Requirements

- n8n (self-hosted or cloud) version 1.0+
- GitHub personal access token with `repo` scope
- Anthropic API key with Claude access
- Discord/Slack webhook URL or SMTP server (for delivery)

## Files

| File | Description |
|------|-------------|
| `weekly-dev-summary.json` | Importable n8n workflow |
| `README.md` | This file |
| `screenshot.png` | Screenshot of successful execution |
