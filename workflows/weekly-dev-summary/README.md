# Weekly GitHub Dev Summary — n8n + Claude Workflow

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API.

## Features

- **Automated weekly trigger** — Runs every Friday at 5pm (configurable)
- **GitHub API integration** — Fetches commits, merged PRs, and closed issues
- **Claude-powered narrative** — Generates human-readable summaries, not just data dumps
- **Multi-channel delivery** — Sends via email AND Slack/Discord webhook
- **Configurable variables** — Repo, destination, language (EN/FR)

## Quick Setup (5 steps)

1. **Import the workflow**: In n8n, go to Workflows → Import → paste `workflow.json`
2. **Add GitHub credentials**: Create an HTTP Header Auth credential named "GitHub Token" with `Authorization: token YOUR_GITHUB_TOKEN`
3. **Add Anthropic credentials**: Create an HTTP Header Auth credential named "Anthropic API Key" with `x-api-key: YOUR_API_KEY`
4. **Configure variables**: Edit the "Fetch Commits" node URL to set your repo owner/name
5. **Set delivery**: Update the email recipient or Slack webhook URL in the final nodes

## Configurable Variables

| Variable | Location | Default | Description |
|----------|----------|---------|-------------|
| `repo_owner` | Fetch nodes URL | `your-org` | GitHub organization/user |
| `repo_name` | Fetch nodes URL | `your-repo` | Repository name |
| `language` | Build Prompt node | `EN` | Summary language (EN/FR) |
| `recipient_email` | Send Email node | `team@yourdomain.com` | Email recipient |
| `webhook_url` | Slack/Discord node | Slack hook URL | Webhook destination |

## Workflow Architecture

```
Weekly Trigger (Friday 5pm)
    ├── Fetch Commits (GitHub API)
    ├── Fetch Merged PRs (GitHub API)
    └── Fetch Closed Issues (GitHub API)
            │
            ▼
    Summarize Commits / PRs / Issues (Code nodes)
            │
            ▼
    Build Claude Prompt (Code node)
            │
            ▼
    Call Claude API (HTTP Request)
            │
            ▼
    Format Output (Code node)
            │
            ├── Send Email
            └── Send to Slack/Discord Webhook
```

## Required Credentials

1. **GitHub Token** (HTTP Header Auth)
   - Header: `Authorization`
   - Value: `token ghp_your_token_here`
   - Scopes needed: `repo` (for private repos) or `public_repo`

2. **Anthropic API Key** (HTTP Header Auth)
   - Header: `x-api-key`
   - Value: `sk-ant-your-key-here`

## Customization

- **Change schedule**: Edit the "Weekly Trigger" node cron expression
- **Add Discord**: Replace the Slack webhook URL with a Discord webhook URL (Discord accepts the same JSON format)
- **Change model**: Edit the "Call Claude API" node body to use a different Claude model
- **Add more data**: Add nodes to fetch GitHub Discussions, releases, etc.
