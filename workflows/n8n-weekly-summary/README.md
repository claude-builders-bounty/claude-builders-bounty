# n8n Weekly Dev Summary — GitHub + Claude API

An n8n workflow that automatically generates a narrative weekly development summary of any GitHub repo using Claude (`claude-sonnet-4-20250514`), delivered via Discord/Slack webhook.

## Setup (5 steps)

### 1. Import the workflow

Open your n8n instance → **Workflows** → **Import from File** → select `workflow.json`.

### 2. Create credentials

**GitHub Token** (HTTP Header Auth):
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer ghp_your_github_token`

**Anthropic API Key** (HTTP Header Auth):
- Name: `Anthropic API Key`
- Header Name: `x-api-key`
- Header Value: `sk-ant-your_api_key`

### 3. Configure environment variables

In n8n → **Settings** → **Variables**, add:

| Variable | Required | Example |
|----------|----------|---------|
| `GITHUB_REPO` | Yes | `vercel/next.js` |
| `SUMMARY_LANGUAGE` | No | `EN` (default) or `FR` |
| `WEBHOOK_URL` | No | `https://discord.com/api/webhooks/...` |

### 4. Assign credentials to nodes

Open each HTTP Request node and select the matching credential:
- GitHub nodes → `GitHub Token`
- Claude API node → `Anthropic API Key`

### 5. Activate

Toggle the workflow **Active**. It runs every Friday at 5 PM (configurable in the cron trigger node).

## How it works

```
Cron (Friday 5pm)
  → Load config (repo, language, webhook)
  → Parallel fetch: commits + closed issues + merged PRs (last 7 days)
  → Aggregate into a structured context object
  → Call Claude API with a narrative summary prompt
  → Extract summary text
  → If webhook URL exists → POST to Discord/Slack
  → Otherwise → log output only
```

## Output structure

Claude generates a narrative with these sections:

1. **Overview** — 2-3 sentences on the week's main focus
2. **Key Changes** — bullet points of important work
3. **Bug Fixes & Maintenance** — if any
4. **Contributors** — who was active
5. **Looking Ahead** — inferred next steps

## Configurable variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | `claude-builders-bounty/claude-builders-bounty` | Target GitHub repository |
| `SUMMARY_LANGUAGE` | `EN` | Summary language (`EN` or `FR`) |
| `WEBHOOK_URL` | *(empty)* | Discord or Slack webhook URL. If empty, output is logged only |

## Delivery options

- **Discord**: Use a Discord webhook URL in `WEBHOOK_URL`
- **Slack**: Use a Slack incoming webhook URL in `WEBHOOK_URL`
- **Email**: Replace the webhook node with n8n's built-in Email node

## Requirements

- n8n instance (self-hosted or n8n Cloud)
- GitHub personal access token (read access to target repo)
- Anthropic API key
- (Optional) Discord or Slack webhook URL
