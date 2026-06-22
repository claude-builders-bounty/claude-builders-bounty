# Weekly Dev Summary — n8n + Claude API

Automatically generate a weekly narrative summary of your GitHub repo's activity using n8n and the Claude API.

## Features

- **Weekly cron trigger** — runs every Friday at 5 PM
- **GitHub data collection** — fetches commits, closed issues, and merged PRs
- **Claude-powered summaries** — uses `claude-sonnet-4-20250514` for natural language generation
- **Multi-language support** — generates summaries in English or French
- **Flexible delivery** — email, Slack, or Discord webhooks
- **Configurable** — set repo, delivery method, and language via variables

## Setup (5 steps)

### 1. Import the workflow

Open n8n and import `weekly-dev-summary.json` via **Workflows > Import from File**.

### 2. Create credentials

In n8n, create two **Header Auth** credentials:
- **GitHub Token**: Header Name = `Authorization`, Value = `Bearer YOUR_GITHUB_TOKEN`
- **Anthropic API Key**: Header Name = `x-api-key`, Value = `YOUR_ANTHROPIC_API_KEY`

### 3. Configure variables

Edit the **Configuration** node and set:
| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Owner/repo format | `octocat/Hello-World` |
| `LANGUAGE` | `EN` or `FR` | `EN` |
| `DELIVERY_METHOD` | `email`, `slack`, or `discord` | `email` |
| `EMAIL_TO` | Recipient email (if using email) | `team@company.com` |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | `https://hooks.slack.com/...` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |

### 4. Link credentials to nodes

- Assign the **GitHub Token** credential to: Fetch Commits, Fetch Closed Issues, Fetch Merged PRs
- Assign the **Anthropic API Key** credential to: Call Claude API

### 5. Activate the workflow

Toggle the workflow **Active**. It will run every Friday at 5 PM and deliver the summary via your chosen method.

## Example Output

```
Weekly Development Summary for my-org/my-repo
============================================

This week, the team made significant progress on the authentication module...
- 15 commits across 4 contributors
- 3 issues closed, including critical bug fixes
- 5 pull requests merged

Key highlights:
- Alice shipped the OAuth2 integration
- Bob fixed the token refresh race condition
...
```

## Architecture

```
┌─────────────────┐
│  Cron Trigger    │  Friday 5 PM
└────────┬────────┘
         ▼
┌─────────────────┐
│  Configuration   │  Set variables
└────────┬────────┘
         ▼
┌─────────────────────────────────────────┐
│  GitHub API (parallel)                  │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ Commits  │ │ Issues   │ │ PRs     │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└────────────────┬────────────────────────┘
                 ▼
        ┌─────────────────┐
        │  Claude API      │  Generate narrative
        └────────┬────────┘
                 ▼
┌─────────────────────────────┐
│  Delivery (conditional)     │
│  ┌───────┐ ┌──────┐ ┌─────┐│
│  │ Email │ │Slack │ │Discord│
│  └───────┘ └──────┘ └─────┘│
└─────────────────────────────┘
```

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token with `repo` scope
- Anthropic API key with Claude API access

## License

MIT
