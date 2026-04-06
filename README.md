# Weekly Dev Summary Workflow 🚀

Automated n8n workflow that generates a weekly narrative summary of your GitHub repository's activity using Claude AI.

## Features

- ✅ **Weekly Cron Trigger** (Every Friday at 5 PM UTC)
- ✅ **GitHub API Integration** (Fetches commits, issues, PRs from the last 7 days)
- ✅ **Claude AI Summary** (Generates a narrative summary using `claude-sonnet-4-20250514`)
- ✅ **Multi-Channel Delivery** (Discord, Slack, or Email)
- ✅ **Fully Configurable** (Repository, API keys, language, notification channels)

---

## Setup (5 Steps)

### 1. Import the Workflow

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `weekly-dev-summary.json`
4. Click **Import**

### 2. Configure GitHub Access

1. Click on the **"Fetch GitHub Activity"** node
2. Under **Authentication**, add your GitHub token:
   - Token: Your GitHub Personal Access Token (with `repo` scope)
3. In the **"Set Variables"** node, update:
   - `GITHUB_REPO`: Your repository (e.g., `octocat/Hello-World`)

### 3. Configure Claude API

1. Get your Claude API key from [Anthropic Console](https://console.anthropic.com/)
2. In the **"Set Variables"** node, update:
   - `CLAUDE_API_KEY`: Your Anthropic API key

### 4. Configure Notification Channel(s)

Choose **one or more** delivery methods:

#### Discord:
- In **"Set Variables"**, add your Discord Webhook URL to `DISCORD_WEBHOOK`
- [How to create a Discord webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)

#### Slack:
- In **"Set Variables"**, add your Slack Webhook URL to `SLACK_WEBHOOK`
- [How to create a Slack webhook](https://api.slack.com/messaging/webhooks)

#### Email:
- Click on the **"Send Email"** node
- Configure your SMTP credentials (host, port, user, password)
- In **"Set Variables"**, set `EMAIL_TO` to your email address

### 5. Activate the Workflow

1. Click **Save** in the top-right corner
2. Toggle the workflow to **Active**
3. Test it manually by clicking **Execute Workflow** (or wait for Friday 5 PM UTC)

---

## Configuration Variables

All variables are set in the **"Set Variables"** node:

| Variable | Description | Example |
|----------|-------------|---------||
| `GITHUB_REPO` | Repository to track (owner/repo) | `facebook/react` |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxx...` |
| `CLAUDE_API_KEY` | Anthropic API Key | `sk-ant-xxx...` |
| `DISCORD_WEBHOOK` | Discord Webhook URL | `https://discord.com/api/webhooks/...` |
| `SLACK_WEBHOOK` | Slack Webhook URL | `https://hooks.slack.com/services/...` |
| `EMAIL_TO` | Email recipient | `team@company.com` |
| `LANGUAGE` | Summary language | `EN`, `FR`, `DE`, etc. |

---

## Example Output

```
Weekly Dev Summary

This week, the team merged 12 pull requests and closed 8 issues. 
The main focus was on improving performance, with 3 PRs related to 
caching optimizations. Notable contributions include:

- @alice fixed a critical bug in the authentication flow (#342)
- @bob added support for dark mode (#351)
- @charlie refactored the API layer for better scalability (#358)

The project saw 47 commits from 6 contributors this week.
```

---

## Customization

### Change the Schedule

Edit the **"Schedule Trigger"** node:
- Current: `0 17 * * 5` (Friday 5 PM UTC)
- Daily: `0 17 * * *` (Every day at 5 PM)
- Monthly: `0 17 1 * *` (First day of the month)

### Fetch More Data

Modify the **"Fetch GitHub Activity"** node:
- Add endpoints: `/repos/{owner}/{repo}/issues` (for issues)
- Add endpoints: `/repos/{owner}/{repo}/pulls` (for PRs)
- Adjust `since` parameter for a custom time window

---

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token (with `repo` scope)
- Anthropic API key (Claude)
- Notification destination (Discord/Slack webhook OR SMTP credentials)

---

## License

MIT

---

**Built with ❤️ by [Neo](https://github.com/neo-sonicseeds) @ SonicSeeds**