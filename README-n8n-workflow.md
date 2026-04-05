# n8n Workflow: Weekly Developer Summary

Automated weekly developer summary that fetches GitHub activity and generates AI-powered narrative summaries delivered to Discord.

## Features

- ⏰ **Weekly Schedule** — Triggers every Friday at 5pm (configurable)
- 📊 **GitHub Integration** — Fetches commits, closed issues, and merged PRs from the past week
- 🤖 **AI Summary** — Uses Claude API (claude-sonnet-4-20250514) to generate narrative summaries
- 💬 **Discord Delivery** — Sends formatted summaries to Discord webhook
- 🌐 **Multilingual** — Supports English (EN) and French (FR) output

## 5-Minute Setup

### Step 1: Import Workflow
1. Open n8n dashboard
2. Click **"Import from File"**
3. Select `n8n-weekly-dev-summary.json`

### Step 2: Configure Variables
In n8n **Settings → Variables**, add these workflow variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Repository path | `owner/repo-name` |
| `GITHUB_TOKEN` | GitHub PAT with `repo` scope | `ghp_xxx...` |
| `GITHUB_API_BASE` | GitHub API base URL | `https://api.github.com` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-xxx...` |
| `CLAUDE_API_URL` | Claude API endpoint | `https://api.anthropic.com/v1/messages` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Summary language | `EN` or `FR` |

### Step 3: Test the Workflow
1. Click **"Test Workflow"** to verify GitHub API connections
2. Confirm data is fetched correctly
3. Verify Claude generates a summary
4. Check Discord receives the message

### Step 4: Activate
Toggle the workflow **ON** to enable weekly execution.

### Step 5: (Optional) Customize Schedule
Edit the Schedule node to change the trigger time/day.

## Acceptance Criteria ✅

- [x] Exportable n8n workflow (.json importable)
- [x] Weekly cron trigger (Friday 5pm)
- [x] Fetches commits, closed issues, merged PRs from GitHub API
- [x] Calls Claude API for narrative summary
- [x] Delivers via Discord webhook
- [x] Configurable: repo, channel, language (EN/FR)
- [x] README with setup in 5 steps

## Example Output

```
📊 Weekly Developer Summary - myorg/myrepo

## Summary

This week the team closed 12 issues, merged 8 PRs, and pushed 45 commits...

## Merged PRs
- #123 Add user authentication
- #124 Fix memory leak in worker

## Closed Issues
- #118 Dashboard not loading
- #119 Update dependencies

## Commits
- abc1234 feat: add OAuth2 support
- def5678 fix: resolve caching issue
```

## License

MIT
