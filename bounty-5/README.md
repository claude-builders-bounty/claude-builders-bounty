# Bounty #5: n8n + Claude Weekly Dev Summary Workflow

Automated weekly development summary powered by n8n and Claude. Fetches commits, closed issues, and merged PRs from GitHub, generates a narrative summary via Claude API, and delivers it to Discord.

## Setup (5 Steps)

### 1. Import Workflow

Open n8n → **Workflows** → **Import from File** → select `weekly-dev-summary.json`

### 2. Configure GitHub API Credential

- Go to **Settings** → **Credentials** → **Add Credential** → **Header Auth**
- Name it `GitHub API`
- Header Name: `Authorization`
- Header Value: `Bearer ghp_YOUR_GITHUB_TOKEN`
- Generate a token at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope

### 3. Configure Claude API Credential

- Add another **Header Auth** credential named `Claude API`
- Header Name: `x-api-key`
- Header Value: `sk-ant-YOUR_CLAUDE_API_KEY`
- Get your key at [console.anthropic.com](https://console.anthropic.com/)

### 4. Set Environment Variables

In your n8n environment (`.env` or docker-compose):

```env
GITHUB_REPO=owner/repo
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK
LANGUAGE=EN          # EN or FR
```

Or edit the **Set Config** node to hardcode values.

### 5. Activate

Click **Active** toggle in n8n. The workflow runs every **Friday at 5pm**.

To test immediately, click **Execute Workflow**.

## Customization

| Setting | Where | Default |
|---------|-------|---------|
| Schedule | Cron Trigger node | Friday 17:00 |
| Repository | Set Config node / `GITHUB_REPO` env | `owner/repo` |
| Language | Set Config node / `LANGUAGE` env | `EN` |
| Webhook URL | Send to Discord node / `DISCORD_WEBHOOK_URL` env | — |
| Claude Model | Claude Summary node body | `claude-sonnet-4-20250514` |

### Slack instead of Discord

Replace the **Send to Discord** node with an **HTTP Request** to your Slack webhook URL, adjusting the JSON body to `{ "text": "..." }`.

## How It Works

```
Cron (Fri 5pm) → Set Config → Fetch Commits + Issues + PRs → Merge → Claude Summary → Discord
```

1. **Cron Trigger** fires weekly
2. **Set Config** computes the date range (last 7 days)
3. Three parallel **GitHub API** calls fetch activity
4. **Merge** combines all data
5. **Claude API** generates a narrative summary
6. **Discord Webhook** delivers the summary

## License

MIT
