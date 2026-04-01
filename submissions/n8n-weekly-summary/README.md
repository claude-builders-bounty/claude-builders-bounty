# Weekly Dev Summary — n8n + Claude

A bounty submission for [claude-builders-bounty/claude-builders-bounty#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5).

## What It Does

Automatically generates a **narrative summary** of your GitHub repository's weekly activity using Claude AI, delivered to your team via Discord, Slack, or email.

**Every Friday at 5pm**, it:
1. 📅 Calculates the date range (past 7 days)
2. 📥 Fetches commits, closed issues, and merged PRs from GitHub
3. 🤖 Calls Claude Sonnet to generate an engaging summary
4. 📤 Delivers it via webhook (Discord/Slack) or email

## Setup (5 Steps)

### 1. Import Workflow
- Open your n8n instance
- Go to **Workflows → Import from File**
- Select `workflow.json`

### 2. Create Credentials
In n8n, create two credentials:

**GitHub Token (HTTP Header Auth):**
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer ghp_YOUR_GITHUB_TOKEN`

**Anthropic API Key:**
- Set in Variables (see step 4)

### 3. Set Variables
In n8n → **Variables**, create:

| Variable | Example Value |
|----------|---------------|
| `GITHUB_API_URL` | `https://api.github.com` |
| `GITHUB_OWNER` | `your-org` |
| `GITHUB_REPO` | `your-repo` |
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `WEBHOOK_URL` | `https://discord.com/api/webhooks/...` |

### 4. Configure Delivery
Set `WEBHOOK_URL` to one of:
- **Discord:** `https://discord.com/api/webhooks/ID/TOKEN`
- **Slack:** Your Slack incoming webhook URL
- **Email:** Modify the final HTTP node to use an email provider

### 5. Activate
Toggle the workflow to **Active**. Summary will fire every Friday at 5pm.

## Configuration

| Setting | Location | Default |
|---------|----------|---------|
| Schedule | Schedule Trigger node | Friday 5pm (`0 17 * * 5`) |
| Claude Model | Call Claude API node | `claude-sonnet-4-20250514` |
| Summary Length | Claude prompt | Under 300 words |
| Max Items | Combine Data node | 20 commits, 20 issues, 20 PRs |

## Example Output

> ## 📊 Weekly Dev Summary
> 
> **my-project** — 03/25/2026 - 04/01/2026
> 
> This week brought significant momentum to the project. The team shipped 23 commits across 5 contributors, closing out 8 issues and merging 3 pull requests...
> 
> Key highlights include the new authentication middleware, which went live after months of planning...

## Architecture

```
Friday 5PM Trigger
    │
    ▼
Prepare Date Range ──┬── Fetch Commits
                     ├── Fetch Closed Issues
                     └── Fetch Merged PRs
                              │
                              ▼
                        Combine Data
                              │
                              ▼
                        Call Claude API
                              │
                              ▼
                        Format Output
                              │
                              ▼
                        Deliver Summary
```

## License

MIT
