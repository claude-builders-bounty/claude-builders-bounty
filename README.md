# n8n GitHub Weekly Summary Workflow

Automatically generates weekly narrative summaries of GitHub activity using Claude API.

## Setup (5 steps)

### 1. Import Workflow

```bash
# In n8n, go to Workflows > Import from File
# Select n8n-github-summary.json
```

### 2. Configure Credentials

Add these credentials in n8n:

**GitHub Token:**
- Name: `GitHub Token`
- Header Name: `Authorization`
- Value: `Bearer YOUR_GITHUB_TOKEN`

**Claude API:**
- Name: `Claude API`  
- API Key: `YOUR_ANTHROPIC_API_KEY`

**SMTP (for email):**
- Configure your email provider settings

### 3. Set Environment Variables

In n8n settings, add:

```bash
GITHUB_REPO=owner/repository
LANGUAGE=EN  # or FR
```

### 4. Test

Click "Execute Workflow" button to test.

### 5. Activate

Toggle the workflow to "Active" - it will run every Friday at 5PM.

## What it does

1. Fetches commits, closed issues, and merged PRs from the past 7 days
2. Sends data to Claude API to generate a narrative summary
3. Emails the summary to configured address

## Customization

### Change Schedule

Edit the cron expression in the trigger node:
```
0 17 * * 5  = Friday 5PM
0 9 * * 1   = Monday 9AM
```

### Use Discord/Slack Instead of Email

Replace the "Send Email" node with:
- Discord webhook node
- Slack node

Just update the message format.

## Screenshot

See `screenshot.png` for example execution.

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub personal access token
- Anthropic API key
- SMTP server (for email delivery)

## Support

For issues, check:
1. Credentials are correct
2. Environment variables are set
3. API keys have necessary permissions
