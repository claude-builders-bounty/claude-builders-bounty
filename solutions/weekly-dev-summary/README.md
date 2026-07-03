# Weekly GitHub Dev Summary — n8n Workflow

Create a complete n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity, using the Claude API.

## Features

- **Weekly cron trigger** — runs every Friday at 5 PM (configurable)
- **Fetches from GitHub API**: commits, closed issues, and merged PRs for the past 7 days
- **Generates narrative summary** via Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- **Dual delivery**: email OR Discord/Slack webhook (configurable)
- **Configurable variables**: GitHub repo, language (EN/FR), delivery channel

## Setup (5 steps)

### 1. Import the workflow

1. Open your n8n instance (self-hosted or cloud)
2. Go to **Workflows** → **Import from File**
3. Select `weekly_github_summary.json`

### 2. Configure environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | ✅ | GitHub personal access token (repo scope) |
| `REPO` | ✅ | GitHub repo in format `owner/repo` (e.g. `vercel/next.js`) |
| `LANG` | ❌ | Output language: `EN` (default) or `FR` |
| `DELIVERY_METHOD` | ❌ | `email` (default) or `discord` |
| `EMAIL_FROM` | For email | Sender email address |
| `EMAIL_TO` | For email | Recipient email address |
| `WEBHOOK_URL` | For Discord | Discord/Slack webhook URL |

### 3. Set up Claude API credentials

In n8n, add your Anthropic API key as a credential of type "Header Auth":
- **Name**: `x-api-key`
- **Value**: `sk-ant-...` (your Anthropic API key)

### 4. Activate the workflow

Toggle the workflow to **Active**. It will run every Friday at 5 PM.

### 5. Test manually

Click **Execute Workflow** to test with your current repo data immediately.

## Output Example

```markdown
## Highlights
- 23 commits across 12 files, with a focus on performance optimization
- 5 issues resolved including a critical authentication bug
- 8 PRs merged, featuring the new dashboard v2

### Commits & Changes
Major refactoring of the API layer reduced response times by 40%...

### Issues Resolved
- #342 Fix login timeout on mobile
- #347 Add pagination to search results

### Merged PRs
- #401 Dashboard redesign (feat/dashboard-v2)
- #405 API rate limiting middleware

### What's Next
The team is working on WebSocket support for real-time updates.
```

## Architecture

```
Weekly Schedule → Date Calculator → GitHub API (3 parallel requests: commits, issues, PRs)
                                                      ↓
                                              Merge Data
                                                      ↓
                                            Prepare Summary
                                                      ↓
                                        Claude API (narrative generation)
                                                      ↓
                                            Format Output
                                                      ↓
                                        Delivery Router
                                        ↙              ↘
                                  Send Email    Send Discord/Slack
```

## Customization

- **Change schedule**: Edit the cron expression in the Weekly Schedule node
- **Add Slack**: Use n8n's Slack node instead of the generic webhook
- **Add more data sources**: Extend the workflow to fetch releases, tags, contributors
- **Change LLM**: Replace Claude with any OpenAI-compatible API
