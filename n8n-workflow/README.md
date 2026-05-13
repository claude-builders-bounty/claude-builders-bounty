# Weekly GitHub Digest — n8n Workflow

A weekly automated summary of your GitHub repo activity, powered by n8n + Claude API.

## Features

- Weekly cron trigger (every Friday 5pm)
- Fetches commits, closed issues, and merged PRs from any GitHub repo
- Generates a narrative summary via Claude API (claude-sonnet-4-20250514)
- Delivers via Slack message **or** email
- Configurable: repo, language, destination channel

## Installation

**5 steps:**

1. **Import the workflow**
   - Open n8n → Workflows → Import from File
   - Select `n8n-workflow/weekly-digest.json`

2. **Set up GitHub credentials**
   - Add a GitHub OAuth2 credential in n8n
   - Scope: `repo` (public repos) or `repo` (private repos)

3. **Set up Claude API key**
   - Add a Header Auth credential in n8n
   - Name: `X-API-Key`, Value: your Anthropic API key

4. **Configure delivery**
   - **Slack**: Add Slack OAuth2 credential, set channel name
   - **Email**: Set SMTP credentials in n8n

5. **Set workflow variables** (edit the Schedule Trigger node)
   - `owner` — GitHub owner (user or org)
   - `repo` — Repository name
   - `language` — Output language (English, Chinese, etc.)
   - `channel` — Slack channel (default: #dev-digest)
   - `email` — Email recipient (fallback delivery)

## Configurable Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `owner` | (required) | GitHub owner |
| `repo` | (required) | GitHub repo name |
| `language` | English | Output language |
| `channel` | #dev-digest | Slack channel |
| `email` | (optional) | Email fallback |

## Output Example

> 📊 **Weekly GitHub Digest**
>
> This week saw 12 commits, 3 closed issues, and 2 merged PRs in myorg/myapp.
>
> Major changes include the new user dashboard (PR #42) by @dev1, improved auth error handling (issue #37), and database migration optimization. Special shoutout to @contributor for the fast review turnaround.
