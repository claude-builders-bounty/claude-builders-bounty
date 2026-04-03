# Weekly Dev Summary with n8n + Claude Code

Automated weekly development summary workflow that collects GitHub activity and generates narrative reports using Claude API.

![Weekly Dev Summary Workflow](docs/workflow-diagram.png)

## Features

- **Automated Scheduling**: Runs weekly on Fridays at 5pm (configurable)
- **GitHub Data Collection**: Fetches commits, closed issues, and merged PRs
- **AI-Powered Summarization**: Uses Claude Sonnet 4 to generate engaging narratives
- **Multi-Channel Delivery**: Discord webhook integration (easily extensible to email/Slack)
- **Multi-Language Support**: English (EN) and French (FR) supported
- **Fully Configurable**: Environment variables for all settings

## Quick Setup (5 Steps)

### Step 1: Install n8n

```bash
# Using Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=your-password \
  -e N8N_HOST=localhost \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n
```

Or use [n8n.cloud](https://n8n.io) for hosted version.

### Step 2: Configure Environment Variables

In n8n, go to **Settings → Variables** and add these:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_API_URL` | GitHub API base URL | `https://api.github.com` |
| `GITHUB_REPO` | Repository (owner/repo) | `claude-builders-bounty/claude-builders-bounty` |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxx` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-api03-xxxxxxxxxxxx` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Summary language | `EN` or `FR` |

### Step 3: Import the Workflow

1. Open n8n at http://localhost:5678
2. Click **Import from File** 
3. Select `n8n-workflow-weekly-dev-summary.json`
4. The workflow will appear in your workflows list

### Step 4: Configure Authentication

1. Click on each GitHub HTTP node
2. Set up **Header Auth** credential:
   - Name: `GitHub Auth`
   - Header Name: `Authorization`
   - Header Value: `Bearer {{$env.GITHUB_TOKEN}}`

### Step 5: Activate & Test

1. Click **Activate** toggle in the top-right
2. Click **Test Workflow** to run immediately
3. Verify Discord receives the summary

## Workflow Structure

```
┌─────────────────────┐
│  Weekly Trigger     │  (Friday 5pm)
│  (Schedule Trigger) │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────┐  ┌──────────┐
│ Since  │  │ Until    │
│ Date   │  │ Date     │
└───┬────┘  └────┬─────┘
    │            │
    └─────┬──────┘
          ▼
    ┌─────────────┬─────────────┬────────────┐
    ▼             ▼             ▼
┌────────┐  ┌──────────┐  ┌──────────┐
│Commits │  │Closed    │  │Merged    │
│        │  │Issues    │  │PRs       │
└───┬────┘  └────┬─────┘  └────┬─────┘
    └────────────┼─────────────┘
                 ▼
        ┌──────────────┐
        │ Prepare Data │
        │ (Code Node)  │
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │ Call Claude  │
        │ API          │
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │ Send to      │
        │ Discord      │
        └──────────────┘
```

## Customization

### Change Delivery Channel

To use email instead of Discord, replace the "Send to Discord" node with the **Gmail** node:

1. Delete "Send to Discord" node
2. Add Gmail node
3. Configure with your credentials
4. Set subject: `Weekly Dev Summary - {{$env.GITHUB_REPO}}`
5. Set body: `{{$json.summary}}`

### Change Schedule

Edit the cron expression in "Weekly Trigger (Friday 5pm)":

| Schedule | Cron Expression |
|----------|-----------------|
| Every Friday 5pm | `0 17 * * 5` |
| Every Monday 9am | `0 9 * * 1` |
| Daily at 6pm | `0 18 * * *` |
| Every Sunday midnight | `0 0 * * 0` |

### Use Different Claude Model

Edit the model in "Call Claude API" node:
- `claude-sonnet-4-20250514` (default)
- `claude-opus-4-20250514` (more capable)
- `claude-haiku-3-5-20250514` (faster/cheaper)

## Troubleshooting

### "401 Unauthorized" on GitHub
- Verify your `GITHUB_TOKEN` has `repo` scope
- Check token hasn't expired

### "401 Unauthorized" on Claude
- Verify `ANTHROPIC_API_KEY` is correct
- Ensure API key has sufficient credits

### No data received
- Check repository name format: `owner/repo`
- Verify the repository has activity in the past week

### Discord not receiving messages
- Verify webhook URL is correct
- Ensure webhook hasn't been deleted

## Files

- `n8n-workflow-weekly-dev-summary.json` - The n8n workflow export
- `README.md` - This setup guide
- `docs/` - Additional documentation

## License

MIT

---

Built for [claude-builders-bounty Issue #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)