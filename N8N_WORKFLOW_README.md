# n8n Weekly Dev Summary — Claude-Powered Automation

Automatically generates a weekly narrative summary of your GitHub repo activity using the Claude API, delivered via Discord or Slack.

## What It Does

Every Friday at 5pm, this n8n workflow:

1. **Fetches** commits, closed issues, and merged PRs from GitHub for the past week
2. **Analyzes** the data using Claude API (Sonnet 4)
3. **Delivers** a human-readable summary to your team via Discord or Slack webhook

## Setup (5 steps)

### 1. Import the workflow

In n8n: **Workflows → Import from File** → select `weekly_dev_summary.json`

### 2. Configure variables

Open the **"Set Variables"** node and update:

| Variable | Value |
|----------|-------|
| `repo` | Your GitHub repo (e.g., `owner/repo`) |
| `github_token` | GitHub Personal Access Token with `repo` scope |
| `anthropic_api_key` | Anthropic/Claude API key (starts with `sk-ant-`) |
| `webhook_url` | Discord or Slack incoming webhook URL |
| `extra_instructions` | (optional) Custom instructions for Claude, e.g. "Keep it professional" |

### 3. Choose your delivery channel

- **Discord**: Enable the "Discord Webhook" node, disable "Slack Webhook"
- **Slack**: Enable "Slack Webhook", disable "Discord Webhook"

### 4. Enable the workflow

Toggle the workflow **Active** switch in n8n.

### 5. Test manually

Click **Execute Workflow** to test immediately. You should receive a summary in your Discord/Slack channel.

## Workflow Structure

```
[Set Variables] 
    ├── [GitHub: Commits] ──┐
    ├── [GitHub: Issues]  ──┤── [Merge & Filter] ── [Claude API] ── [Format] ──┬── [Discord]
    └── [GitHub: PRs]     ──┘                                                  └── [Slack]
```

## Sample Output

```
📊 Weekly Dev Summary — claude-builders-bounty/claude-builders-bounty
Week: 2026-05-16 to 2026-05-23

🚀 Commits: 12
🐛 Issues Closed: 5
✅ PRs Merged: 8

🔹 Highlights
• Added CHANGELOG generator skill by @contributor1
• Fixed memory leak in pre-tool-use hook by @contributor2  
• New CLAUDE.md template for Next.js projects

🔧 Active Contributors
@alice (4 commits), @bob (3 commits), @carol (2 commits)
```

## Requirements

- n8n instance (self-hosted or n8n.cloud)
- GitHub Personal Access Token
- Anthropic API key
- Discord or Slack webhook URL

## Customization

- **Schedule**: Edit the "Friday 5pm" trigger node to change the cron expression
- **Language**: Add `"Respond in French"` to `extra_instructions` for French output
- **Channel**: Add more webhook nodes for multi-channel delivery

## License

MIT
