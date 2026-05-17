# n8n Weekly GitHub Summary with Claude

> Automated weekly dev summary workflow — GitHub activity → Claude narrative → Discord/Email.  
> Built for [Claude Builders Bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) ($200)

## Quick Setup (5 Steps)

### 1. Import the workflow

In your n8n instance, go to **Workflows → Import from File** and select `n8n-weekly-summary.json`.

### 2. Configure GitHub

Edit the **Set Date Range & Repo** node and update:
```
repo_owner: "your-org"
repo_name: "your-repo"
```

### 3. Add your Anthropic API key

In n8n, go to **Credentials → Add Credential → Header Auth**:
- Name: `Anthropic API`
- Header Name: `x-api-key`
- Header Value: `sk-ant-...` (your Claude API key)

Then assign this credential to the **Generate Summary with Claude** node.

### 4. Choose delivery method

**Option A — Discord Webhook:**
1. Create a webhook in your Discord server (Server Settings → Integrations → Webhooks)
2. Set the URL in the **Send to Discord** node's `webhook_url` field
3. Disable the **Send Email** node (click it → toggle off)

**Option B — Email:**
1. Configure n8n's email node with your SMTP settings
2. Set `to_email` in the **Extract Summary Text** node
3. Disable the **Send Discord** node

### 5. Activate

Click **Activate** (the toggle in the top-right). The workflow runs every Friday at 5pm.

## What It Does

```
┌─────────────┐    ┌──────────────┐    ┌──────────┐    ┌─────────┐
│ Weekly Cron │───▶│ GitHub API   │───▶│ Merge    │───▶│ Claude  │
│ (Fri 5pm)   │    │ commits,     │    │ Data     │    │ API     │
│             │    │ issues, PRs  │    │          │    │         │
└─────────────┘    └──────────────┘    └──────────┘    └────┬────┘
                                                            │
                                              ┌─────────────┴──────────┐
                                              ▼                        ▼
                                        ┌──────────┐            ┌──────────┐
                                        │ Discord  │            │  Email   │
                                        │ Webhook  │            │          │
                                        └──────────┘            └──────────┘
```

## Configuration

| Variable | Location | Description |
|---|---|---|
| `repo_owner` | Set Date Range node | GitHub org/user |
| `repo_name` | Set Date Range node | GitHub repo name |
| `language` | Set Date Range node | `"EN"` or `"FR"` |
| `webhook_url` | Send to Discord node | Discord webhook URL |
| `to_email` | Extract Summary node | Recipient email |

## Sample Output

```markdown
## Weekly Summary — owner/repo (2026-05-17)

### Overview
This week saw 23 commits across 5 contributors, with a focus on
authentication improvements and bug fixes. 3 PRs were merged and
8 issues were closed.

### Key Changes
- Refactored auth module to use session tokens instead of JWT
- Fixed memory leak in WebSocket handler (was holding 2KB per connection)
- Added rate limiting on login endpoint (5 requests/minute/IP)
- Updated all dependencies to latest minor versions

### Merged PRs
- #1520: Pre-tool-use hook for destructive bash commands (by ouzegba-lgtm)
- #1521: Fix race condition in payment webhook (by alice)
- #1522: Add health check endpoint (by bob)

### Issues Closed
- #150: Login page flashes on slow connections
- #151: PaymentIntent not found after webhook timeout
- #152: Missing error boundary on dashboard

### Next Week
Focus on shipping the billing dashboard and writing integration tests.
```

## Requirements

- **n8n** v1.0+ (self-hosted or cloud)
- **Anthropic API key** (Claude Sonnet 4 recommended)
- **Discord webhook** OR **SMTP server** (for delivery)

---

*🤖 Built as part of Claude Builders Bounty Program*
