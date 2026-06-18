# Claude Weekly Dev Summary — n8n Workflow 🤖

A complete [n8n](https://n8n.io) workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

**Bounty:** #5 — $200

## Architecture

```
Schedule (Fri 5pm)
     │
     ▼
Set Config ──┬──► GitHub Commits (past 7 days)
             ├──► GitHub Closed Issues
             └──► GitHub Merged PRs
                      │
                      ▼
                 Merge & Split
                      │
                      ▼
                 Prepare Prompt
                      │
                      ▼
                 Claude API (claude-sonnet-4-20250514)
                      │
                      ▼
                 Deliver via Webhook (Slack/Discord)
```

## Installation (5 Steps)

### 1. Install n8n

```bash
npm install -g n8n
n8n start
```

Open http://localhost:5678 in your browser.

### 2. Import the workflow

From the n8n UI:
- Click **Workflows** → **Import from File**
- Select `claude-weekly-summary.json`

Or via CLI:
```bash
# Copy to n8n's import directory
cp claude-weekly-summary.json ~/.n8n/
```

### 3. Configure credentials

You need to set up **two credentials** in n8n:

**GitHub API (Header Auth):**
| Field | Value |
|-------|-------|
| Name | `Authorization` |
| Value | `Bearer ghp_your_github_token` |

**Claude API (Header Auth):**
| Field | Value |
|-------|-------|
| Name | `x-api-key` |
| Value | `sk-ant-your_claude_api_key` |

### 4. Configure variables

Edit the **Set Config** node with your values:

| Variable | Description | Default |
|----------|-------------|---------|
| `repo` | GitHub repo (`owner/repo-name`) | `owner/repo-name` |
| `language` | Output language (`EN`/`FR`) | `EN` |
| `webhook_url` | Slack/Discord webhook URL | *(your webhook)* |
| `github_token` | GitHub personal access token | *(your token)* |

### 5. Activate

Click **Active** toggle on the workflow. It will run every Friday at 5 PM UTC.

For a manual test, click **Execute Workflow**.

## Output Example

```
## Weekly Dev Summary — 2026-06-18

### 📝 Commits
- [a1b2c3d] feat: add user authentication (Alice)
- [e4f5g6h] fix: resolve pagination bug (Bob)

### ✅ Issues Closed
- #42 Fix login redirect loop
- #43 Add rate limiting to API

### 🎉 Merged PRs
- #45 Refactor auth middleware by @alice
- #46 Add unit tests for API by @bob

### 🔍 Key Themes
This week the team focused on authentication improvements
and API stability. Two significant bugs were fixed in the
payment processing pipeline.
```

## Customization

- **Change schedule**: Edit the **Weekly Cron** node's cron expression
- **Add delivery methods**: Add an Email node (SMTP) after Claude API
- **Change language**: Set `language` to `FR` for French output
- **Filter by labels**: Modify the GitHub query parameters in each fetch node

## Requirements

- n8n (v2.x+) — [Install guide](https://docs.n8n.io/hosting/installation/)
- GitHub personal access token with `repo` scope
- Anthropic API key with Claude Sonnet 4 access
- Slack webhook URL (or Discord/SMTP for alternative delivery)
