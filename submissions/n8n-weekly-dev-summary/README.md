# n8n + Claude API — Automated Weekly Dev Summary

> **Bounty #5** — $200 WORKFLOW: n8n + Claude Code — automated weekly dev summary

Automatically generates a narrative weekly summary of a GitHub repo's activity using the Claude API, delivered via email or Discord/Slack webhook.

## Features

- 🔄 **Weekly cron trigger** (every Friday at 5PM, configurable)
- 📊 **Fetches from GitHub API**: commits, closed issues, merged PRs
- 🤖 **Claude API powered**: uses `claude-sonnet-4-20250514` for narrative generation
- 📧 **Dual delivery**: email (SMTP) or Discord/Slack webhook
- 🌍 **Multilingual**: configurable output language (EN/FR)
- ⚙️ **Fully configurable**: all repos, channels, and settings via workflow variables

## Setup (5 Steps)

### Prerequisites
- An [n8n instance](https://docs.n8n.io) (self-hosted or cloud)
- GitHub Personal Access Token (with `repo` scope)
- Anthropic API Key
- SMTP credentials (for email delivery) OR a Discord/Slack webhook URL

### Step 1: Import the Workflow

1. Open your n8n instance
2. Click **"Import from File"**
3. Select `weekly-dev-summary.json`

### Step 2: Configure Credentials

Create three credentials in n8n (Settings → Credentials):

| Credential | Type | Value |
|---|---|---|
| `GitHub Token` | Header Auth | Name: `Authorization`, Value: `Bearer ghp_YOUR_TOKEN` |
| `Anthropic API Key` | Header Auth | Name: `x-api-key`, Value: `sk-ant-YOUR_KEY` |
| `SMTP Account` *(email only)* | SMTP | Your email server settings |

Then assign them to the corresponding nodes:
- **Fetch Commits / Issues / PRs** → GitHub Token
- **Claude API Call** → Anthropic API Key
- **Send via Email** → SMTP Account *(skip if using webhook)*

### Step 3: Set Workflow Variables

Go to **Workflow → Settings → Variables** and set:

| Variable | Required | Default | Description |
|---|---|---|---|
| `GITHUB_REPO` | ✅ | — | Repository in `owner/repo` format (e.g., `facebook/react`) |
| `DELIVERY_METHOD` | ✅ | `webhook` | `email` or `webhook` |
| `WEBHOOK_URL` | if webhook | — | Discord/Slack webhook URL |
| `DESTINATION_EMAIL` | if email | — | Recipient email address |
| `SENDER_EMAIL` | if email | `dev-summary@example.com` | Sender email address |
| `OUTPUT_LANGUAGE` | — | `EN` | `EN` for English, `FR` for French |
| `CLAUDE_MODEL` | — | `claude-sonnet-4-20250514` | Claude model to use |
| `GITHUB_API_URL` | — | `https://api.github.com` | GitHub API base URL (change for GHES) |

### Step 4: Customize the Schedule

The default trigger runs **every Friday at 5PM**. To change:
- Open the **"Every Friday 5PM"** node
- Modify the cron expression:
  - Monday 9AM: `0 9 * * 1`
  - Daily 6PM: `0 18 * * *`
  - Last day of month: `0 17 L * *`

### Step 5: Test and Activate

1. Click **"Test Workflow"** to run manually
2. Verify the output in the delivery channel
3. Click **"Activate"** to enable the scheduled trigger

## Workflow Architecture

```
[Schedule Trigger] ──→ [Fetch Commits]
                   ──→ [Fetch Issues]    ──→ [Merge] ──→ [Process] ──→ [Claude API] ──→ [Extract] ──→ [Route]
                   ──→ [Fetch PRs]                                                                     ├─→ [Email]
                                                                                                      └─→ [Webhook]
```

## Generated Summary Structure

The Claude-generated summary includes:

1. **Executive Summary** — 2-3 sentence overview
2. **Key Changes** — Grouped by theme with bullet points
3. **Issues Resolved** — Impactful closed issues highlighted
4. **Contributor Spotlight** — Top contributors recognized
5. **Looking Ahead** — Suggested focus areas

## Sample Output

```markdown
## 📅 Weekly Dev Summary: myorg/myproject
**Week: 2026-05-07 → 2026-05-14**

### Executive Summary
This week saw significant progress on the authentication module, with 3 PRs merged
adding OAuth2 support and 2FA. The team resolved 5 issues including a critical
session expiry bug.

### Key Changes
- **Authentication Overhaul**: Added OAuth2 with Google/GitHub providers (#342)
- **Performance**: Reduced API response time by 40% through query optimization (#338)
- ...

### Issues Resolved
- #331: Session expiry not respected on mobile browsers
- ...

### Contributor Spotlight
- Alice: 12 commits, 3 PRs
- Bob: 8 commits, 2 PRs

### Looking Ahead
With auth complete, next week should focus on the dashboard redesign sprint...
```

## Troubleshooting

| Issue | Solution |
|---|---|
| Empty data results | Verify `GITHUB_REPO` is set and token has `repo` scope |
| Claude API errors | Check API key and ensure model name is correct |
| Email not sending | Verify SMTP credentials and `SENDER_EMAIL` |
| Webhook 400 error | Ensure `WEBHOOK_URL` is a valid Discord/Slack webhook |
| Too many commits | Reduce by adjusting the `per_page` parameter |

## Files

| File | Description |
|---|---|
| `weekly-dev-summary.json` | Importable n8n workflow |
| `README.md` | This file |

## License

MIT
