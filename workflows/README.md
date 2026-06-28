# n8n + Claude API: Weekly GitHub Summary Workflow

Automated workflow that generates narrative summaries of GitHub repository activity using Claude AI.

## Features

✅ **Weekly Automation**: Runs every Friday at 5pm (configurable)  
✅ **GitHub Integration**: Fetches commits, closed issues, merged PRs  
✅ **Claude AI**: Generates narrative summary via Claude API (claude-sonnet-4-20250514)  
✅ **Multi-Channel Delivery**: Discord webhook OR Email (configurable)  
✅ **Configurable**: Repository, language (EN/FR), destination  
✅ **Exportable**: Import JSON workflow into any n8n instance  

## Setup (5 Steps)

### 1. Install n8n

```bash
# Docker (recommended)
docker run -d --name n8n -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n

# Or npm
npm install -g n8n
n8n start
```

Access n8n at `http://localhost:5678`

### 2. Import Workflow

1. Download `n8n-weekly-summary.json` from this repo
2. In n8n, click **Workflows** → **Import from File**
3. Select the JSON file
4. Workflow appears in your list

### 3. Configure Credentials

**GitHub API:**
1. Go to **Credentials** → **New Credential**
2. Select **HTTP Header Auth**
3. Name: `GitHub API`
4. Set:
   - Name: `Authorization`
   - Value: `Bearer YOUR_GITHUB_TOKEN`
5. Save and assign to all GitHub nodes

**Claude API:**
1. Go to **Credentials** → **New Credential**
2. Select **HTTP Header Auth**
3. Name: `Claude API`
4. Set:
   - Name: `x-api-key`
   - Value: `YOUR_ANTHROPIC_API_KEY`
5. Save and assign to Claude node

### 4. Set Environment Variables

In n8n **Settings** → **Environment Variables**:

```bash
GITHUB_REPO=owner/repo              # Your GitHub repository
SUMMARY_LANGUAGE=EN                 # EN or FR
WEBHOOK_URL=https://discord.com/api/webhooks/...  # Discord webhook
EMAIL_FROM=noreply@example.com      # Sender email
EMAIL_TO=team@example.com           # Recipient email
```

### 5. Activate Workflow

1. Open the workflow
2. Toggle **Active** switch (top right)
3. Set schedule: **Every week on Friday at 5:00 PM**
4. Save

Workflow runs automatically every week!

## Manual Testing

1. Open workflow in n8n
2. Click **Execute Workflow** (bottom left)
3. Check execution logs for each node
4. Verify summary delivered to Discord/Email

## Workflow Structure

```
Weekly Trigger (Schedule)
    ↓
Set Configuration (env vars)
    ↓
┌───────────────────┬───────────────────┬───────────────────┐
│ Fetch Commits     │ Fetch Issues      │ Fetch PRs         │
└───────────────────┴───────────────────┴───────────────────┘
    ↓
Aggregate Data (Code node)
    ↓
Generate Summary with Claude (API call)
    ↓
Extract Summary (Code node)
    ↓
┌───────────────────┬───────────────────┐
│ Send to Discord   │ Send via Email    │
└───────────────────┴───────────────────┘
```

## Customization

### Change Schedule
Edit **Weekly Trigger** node → adjust interval

### Change Language
Set `SUMMARY_LANGUAGE=FR` in environment variables

### Add Slack Integration
Add new HTTP Request node after **Extract Summary**:
- Method: POST
- URL: Your Slack webhook URL
- Body: `{ "text": "={{ $json.summary }}" }`

### Modify Summary Format
Edit **Aggregate Data** node → change prompt instructions

## Troubleshooting

**GitHub API 401:**
- Check token has `repo` scope
- Verify credential assigned to all GitHub nodes

**Claude API Error:**
- Verify API key is valid
- Check rate limits (Anthropic dashboard)
- Ensure model name is correct: `claude-sonnet-4-20250514`

**No Data Returned:**
- Verify `GITHUB_REPO` format: `owner/repo`
- Check date range (last 7 days)
- Test GitHub API manually: `curl -H "Authorization: Bearer TOKEN" https://api.github.com/repos/owner/repo/commits`

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token
- Anthropic API key
- Discord webhook URL OR SMTP credentials

## Resources

- [n8n Documentation](https://docs.n8n.io)
- [Claude API Docs](https://docs.anthropic.com)
- [GitHub API Docs](https://docs.github.com/en/rest)

## License

MIT
