# Weekly Dev Summary Agent — Usage

## Install

```bash
cp weekly-dev-summary.js .claude/hooks/weekly-dev-summary.js
```

## Run

```bash
# Generate summary (prints to stdout)
node weekly-dev-summary.js --days 7

# Post to n8n webhook
node weekly-dev-summary.js --webhook-url https://n8n.example.com/webhook/weekly-summary --days 7 --post

# Using environment variable
export N8N_WEBHOOK_URL=https://n8n.example.com/webhook/weekly-summary
node weekly-dev-summary.js --post
```

## n8n Setup

1. Create a new n8n workflow
2. Add a **Webhook** trigger node (HTTP Method: POST)
3. Copy the webhook URL
4. Add downstream nodes: Slack, Discord, Email, Telegram, etc.
5. Run the agent with `--webhook-url <url> --post`

## As Claude Code Skill

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "command": "node .claude/hooks/weekly-dev-summary.js --webhook-url $N8N_WEBHOOK_URL --days 7 --post"
      }
    ]
  }
}
```

## Test

```bash
node test-weekly.js
```

Creates a temp repo with synthetic commits across a week and verifies summary generation.
