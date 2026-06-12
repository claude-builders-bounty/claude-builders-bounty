# Weekly Dev Summary — n8n + Claude API Workflow

Automatically generates a narrative summary of your GitHub repo's weekly activity using the Claude API.

## Setup (5 steps)

### 1. Import the workflow
1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `weekly-dev-summary.json`

### 2. Set environment variables
In n8n, go to **Settings** → **Environment Variables** and add:

| Variable | Description | Example |
|----------|-------------|---------|
| `REPO_OWNER` | GitHub org/user | `your-org` |
| `REPO_NAME` | Repository name | `your-repo` |
| `GH_TOKEN` | GitHub PAT with repo scope | `ghp_...` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-...` |
| `SLACK_WEBHOOK_URL` | Slack webhook (optional) | `https://hooks.slack.com/...` |
| `DISCORD_WEBHOOK_URL` | Discord webhook (optional) | `https://discord.com/api/...` |
| `SUMMARY_LANGUAGE` | Output language | `EN` or `ZH` |

Or configure these directly in the **Set Configuration** node.

### 3. Activate the workflow
Click the **Active** toggle in the top-right of the workflow editor.

### 4. Verify delivery
The workflow triggers every **Friday at 5:00 PM**. You'll receive:
- Weekly commit log (up to 20 most recent)
- Closed issues (up to 15)
- Merged PRs (up to 15)
- AI-generated narrative summary via Claude API

### 5. Customize (optional)
Edit the **Format Data for Claude** Code node to adjust:
- How many commits/issues/PRs to include
- The prompt template for Claude
- Add filtering by labels or authors

## Workflow Diagram

```
Schedule ──→ Set Config ──┬──→ Fetch Commits ──┐
                          ├──→ Fetch Issues  ──┤
                          └──→ Fetch PRs ──────┤
                                               ▼
                                        Format Data ──→ Claude API ──→ Format ──→ Route ─┬→ Slack
                                                                                         └→ Discord
```

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token
- Anthropic API key (for Claude API)
- Slack webhook URL **or** Discord webhook URL

## Configuration

All variables are configurable via environment variables or the **Set Configuration** node. The workflow uses sensible defaults — just change `REPO_OWNER` and `REPO_NAME` to get started.
