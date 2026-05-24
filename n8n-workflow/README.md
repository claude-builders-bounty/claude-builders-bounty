# n8n + Claude: Automated Weekly Dev Summary

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

## Setup (5 steps)

### 1. Import the Workflow

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `workflow.json`

### 2. Configure GitHub Token

1. Go to **Settings** → **Credentials** → **Add Credential**
2. Choose **Header Auth**
3. Name: `GitHub Token`
4. Header Name: `Authorization`
5. Header Value: `token YOUR_GITHUB_TOKEN`

### 3. Configure Claude API Key

1. Go to **Settings** → **Credentials** → **Add Credential**
2. Choose **Header Auth**
3. Name: `Claude API Key`
4. Header Name: `x-api-key`
5. Header Value: `YOUR_ANTHROPIC_API_KEY`
6. Add another header: `anthropic-version: 2023-06-01`

### 4. Edit Configuration

Open the **Configuration** node and edit:

```javascript
const CONFIG = {
  GITHUB_OWNER: "your-org",      // ← Change this
  GITHUB_REPO: "your-repo",      // ← Change this
  DELIVERY_METHOD: "webhook",     // 'email' or 'webhook'
  WEBHOOK_URL: "https://discord.com/api/webhooks/...",  // Your webhook
  EMAIL_TO: "team@example.com",   // If using email
  LANGUAGE: "en",                 // 'en' or 'fr'
  DAYS_BACK: 7
};
```

### 5. Activate

Toggle the workflow to **Active**. It will run every Friday at 5pm UTC.

## How It Works

```
┌─────────────────┐
│  Weekly Trigger  │ (Friday 5pm UTC)
│  (Cron)          │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Config  │ (GitHub repo, delivery method, language)
    └────┬────┘
         │
    ┌────┴──────────────────────┐
    │              │              │
┌───▼───┐   ┌─────▼─────┐  ┌────▼────┐
│Commits│   │  Issues   │  │   PRs   │
│(GitHub)│  │ (GitHub)  │  │ (GitHub)│
└───┬───┘   └─────┬─────┘  └────┬────┘
    │              │              │
┌───▼───┐   ┌─────▼─────┐  ┌────▼────┐
│Format │   │  Format   │  │ Format  │
└───┬───┘   └─────┬─────┘  └────┬────┘
    │              │              │
    └──────────────┼──────────────┘
                   │
            ┌──────▼──────┐
            │ Build Prompt │
            └──────┬──────┘
                   │
            ┌──────▼──────┐
            │ Call Claude  │
            │   API        │
            └──────┬──────┘
                   │
            ┌──────▼──────┐
            │Format Output │
            └──────┬──────┘
                   │
            ┌──────▼──────┐
            │  Delivery    │
            │  (Webhook    │
            │   or Email)  │
            └─────────────┘
```

## Delivery Options

### Discord Webhook
1. Create a webhook in your Discord channel
2. Set `DELIVERY_METHOD: "webhook"`
3. Set `WEBHOOK_URL` to your Discord webhook URL

### Slack Webhook
1. Create a Slack app with Incoming Webhooks
2. Set `DELIVERY_METHOD: "webhook"`
3. Set `WEBHOOK_URL` to your Slack webhook URL

### Email
1. Set `DELIVERY_METHOD: "email"`
2. Set `EMAIL_TO` to recipient(s)
3. Configure n8n's email credentials

## Customization

- **Change schedule**: Edit the cron expression in the trigger node
- **Change model**: Edit the model in the Claude API node (e.g., `claude-sonnet-4-20250514`)
- **Change prompt**: Edit the prompt template in the "Build AI Prompt" node
- **Add more repos**: Duplicate the workflow for each repo

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token (with `repo` scope)
- Anthropic API key
- Webhook URL OR email configuration
