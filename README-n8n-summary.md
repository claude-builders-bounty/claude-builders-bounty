# Weekly GitHub Dev Summary — n8n Workflow

Generate an AI-powered narrative summary of your repo's weekly activity, delivered to Slack every Friday at 5 PM.

## Setup (5 Steps)

**Step 1.** Install [n8n](https://docs.n8n.io/choose-n8n/) (cloud or self-hosted).

**Step 2.** Import the workflow:
- Open n8n → **Workflows** → **Import from File**
- Select `weekly-dev-summary.json`

**Step 3.** Add your secrets as n8n **Environment Variables** (Settings → Environment Variables):

| Variable | Value |
|----------|-------|
| `GITHUB_TOKEN` | GitHub personal access token with `repo` scope |
| `CLAUDE_API_KEY` | Anthropic API key |

**Step 4.** Configure the **Configuration** node:
- `githubRepo`: `owner/repo-name`
- `slackChannel`: `#dev-summary` (or any Slack channel)
- `language`: `EN` or `FR`
- `claudeModel`: `claude-sonnet-4-20250514` (default)

**Step 5.** Set up [Slack webhook](https://api.slack.com/messaging/webhooks) in the last node. Click **Test Workflow** → it fetches last 7 days and sends a summary.

## How It Works

```
Friday 5 PM → GitHub API → Claude API → Slack
     ↓           ↓           ↓           ↓
  Trigger   Fetch commits,  Write     Post formatted
            issues, PRs    summary    Slack message
```

## Configurable Variables

| Node | What to change |
|------|----------------|
| Configuration | repo, channel, language, model |
| Build Date Filters | default: last 7 days |
| Claude API | system prompt, max tokens |
| Slack Webhook | message format, channel |
