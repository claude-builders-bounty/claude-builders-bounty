# Weekly GitHub Dev Summary - n8n Workflow

Generate weekly development summaries for your GitHub repositories using Claude API, delivered via Discord or Email.

## Features

- ⏰ **Weekly Schedule**: Runs every Friday at 5:00 PM
- 📊 **GitHub Data**: Fetches commits, closed issues, and merged PRs from the last 7 days
- 🤖 **AI-Powered**: Uses Claude API to generate narrative summaries
- 📬 **Flexible Delivery**: Discord webhook or Email
- 🌐 **Multilingual**: Supports English (EN) and French (FR)

## Setup (5 Steps)

### Step 1: Install n8n
```bash
npm install -g n8n
```

### Step 2: Import the Workflow
1. Open n8n (`n8n start`)
2. Go to **Workflows** → **Import from File**
3. Select `workflow.json`

### Step 3: Configure GitHub Credentials
1. Create a GitHub Personal Access Token at https://github.com/settings/tokens
2. In n8n, go to **Credentials** → **New** → **Header Auth**
3. Name it `github-auth` and add your token

### Step 4: Configure Claude API
1. Get your Claude API key from https://console.anthropic.com/
2. In n8n, install `@n8n/n8n-nodes-langchain` if not already available
3. Add your Claude API key to the `Claude Summary Generation` node

### Step 5: Set Configuration Values
Edit the **Configuration** node with your values:

| Field | Description | Example |
|-------|-------------|---------|
| `githubRepo` | Repository in format `owner/repo` | `claude-builders-bounty/claude-builders-bounty` |
| `githubToken` | Your GitHub Personal Access Token | `ghp_xxxxx` |
| `discordWebhook` | Discord webhook URL (or leave empty) | `https://discord.com/api/webhooks/...` |
| `emailTo` | Email recipient (or leave empty) | `team@example.com` |
| `emailHost` | SMTP server host | `smtp.gmail.com` |
| `emailPort` | SMTP port | `587` |
| `emailUser` | SMTP username | `your-email@gmail.com` |
| `emailPass` | SMTP password or app password | `xxxx xxxx xxxx xxxx` |
| `language` | Summary language | `EN` or `FR` |
| `deliveryMethod` | `discord` or `email` | `discord` |

### Activate the Workflow
Toggle the workflow to **Active** in n8n. It will run automatically every Friday at 5 PM.

## Workflow Structure

```
Schedule Trigger (Friday 5PM)
    ↓
Configuration (Set Variables)
    ↓
┌───────────┬────────────┐
↓           ↓            ↓
Commits    Issues       PRs
API        API          API
↓           ↓            ↓
Process    Process     Process
Commits    Issues      PRs
└───────────┴────────────┘
    ↓
Merge Data
    ↓
Claude Summary Generation
    ↓
┌───────────┬────────────┐
↓           ↓            ↓
Discord    Email        (both if configured)
Webhook
```

## Environment Variables (Alternative)

Instead of hardcoding in the Configuration node, use n8n environment variables:

- `GITHUB_REPO`
- `GITHUB_TOKEN`
- `DISCORD_WEBHOOK`
- `EMAIL_TO`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `SUMMARY_LANGUAGE`

## Troubleshooting

**Workflow not triggering?**
- Verify the cron schedule is set to Friday at 17:00
- Ensure the workflow is activated (toggle switch ON)

**GitHub API errors?**
- Check your Personal Access Token has `repo` scope for private repos
- Verify the repository name format is `owner/repo`

**Claude summary not generating?**
- Confirm your Claude API key is valid
- Check the LangChain node configuration

**Discord/Email not sending?**
- Verify webhook URL is correct
- For email, ensure SMTP credentials are correct and 2FA is disabled for Gmail

## License

MIT
