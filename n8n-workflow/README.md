# GitHub Weekly Summary — n8n + Claude

Automated weekly narrative summary of GitHub repository activity, powered by Claude AI.

## What It Does

📊 Every Friday at 5PM, this workflow:
1. Fetches weekly commits, closed issues, and merged PRs from GitHub API
2. Sends the data to Claude API for narrative summary generation
3. Delivers the summary via Discord webhook OR email

## Setup (5 Steps)

### Step 1: Import Workflow
- Open n8n → Click "Import from File"
- Select `github-weekly-summary.json`

### Step 2: Configure Variables
In n8n Variables panel, set:

| Variable | Value |
|----------|-------|
| `GITHUB_REPO` | `owner/repo-name` (e.g., `openclaw/openclaw`) |
| `GITHUB_TOKEN` | `ghp_xxxx` (GitHub PAT with `repo` scope) |
| `ANTHROPIC_API_KEY` | `sk-ant-xxxx` (Anthropic API key) |
| `DELIVERY_WEBHOOK_URL` | Discord webhook URL (or leave empty) |
| `EMAIL_TO` | Your email (or leave empty) |
| `LANGUAGE` | `EN` or `FR` |

### Step 3: Add GitHub Credentials
- n8n HTTP Request node → "Authentication" → "Header Auth"
- Name: `Authorization`
- Value: `token {{ $vars.GITHUB_TOKEN }}`

### Step 4: Test the Workflow
- Click "Test Workflow" to verify it works
- Check Discord/email for the summary

### Step 5: Activate
- Toggle workflow ON
- It runs automatically every Friday at 5PM

## Configuration Options

### Delivery Methods
Choose ONE by enabling the corresponding node:
- **Discord**: Set `DELIVERY_WEBHOOK_URL` and enable "Send to Discord" node
- **Email**: Set `EMAIL_TO` and enable "Send Email" node

### Language
Set `LANGUAGE` to:
- `EN` — English summary
- `FR` — French summary

## Troubleshooting

**No commits fetched?**
→ Verify `GITHUB_TOKEN` has `repo` scope

**Claude API error?**
→ Check `ANTHROPIC_API_KEY` is valid

**Discord webhook not working?**
→ Ensure webhook URL is a valid Discord webhook (starts with `https://discord.com/api/webhooks/`)

## License

MIT
