# n8n + Claude Code — Automated Weekly Dev Summary

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

**Bounty:** $200 — https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5

## Features

- Weekly cron trigger (Friday at 5pm)
- Fetches commits, closed issues, and merged PRs from GitHub API
- Generates a narrative summary via Claude API (`claude-sonnet-4-20250514`)
- Delivers via Discord webhook
- Fully configurable: repo, webhook URL, language

## Quick Setup (5 Steps)

### 1. Import the workflow
- Open n8n → **Workflows** → **Add Workflow** → **Import from File**
- Select `weekly-dev-summary.json`

### 2. Set your GitHub token
- Create a credential: **GitHub API** (Personal Access Token)
- Add your `GITHUB_TOKEN`

### 3. Set your Claude API key
- Create a credential: **HTTP Request** (Header Auth)
- Add your `ANTHROPIC_API_KEY` as `x-api-key`

### 4. Configure variables
Edit the **Set Variables** node:

| Variable | Description | Default |
|----------|-------------|---------|
| `repo` | GitHub repo (owner/name) | `owner/repo` |
| `discordWebhook` | Discord webhook URL | Your webhook URL |
| `language` | Summary language | `EN` |

### 5. Activate the workflow
Toggle **Active** on. The workflow runs every Friday at 5pm.

## Manual Trigger

Click **Execute Workflow** to test immediately.

## Output Example

```markdown
## Weekly Dev Summary — owner/repo
*Week of May 21 – May 28, 2026*

**Commits:** 12 commits across 4 contributors
**Issues Closed:** 3
**PRs Merged:** 5

### Highlights
- Authentication refactor completed — migrated from JWT to session-based auth
- Performance improvements on search endpoint (p95 latency reduced by 40%)
- Two new contributors joined the project 🎉

### Key Metrics
- Lines added: 2,450
- Lines removed: 1,200
- Active branches: 8
```

## Delivery Channels

Default: **Discord webhook**. To switch to email or Slack, replace the Webhook node:
- **Email**: use n8n's Email node (SMTP)
- **Slack**: use Slack node with incoming webhook
