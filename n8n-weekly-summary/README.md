# Weekly GitHub Summary - n8n Workflow

Automated weekly summary report generator for GitHub repositories using n8n, GitHub API, and Claude AI.

## Overview

This workflow automatically collects weekly activity from your GitHub repository and generates a narrative summary using Claude AI (claude-sonnet-4-20250514), delivering it via Discord webhook and/or Email.

### Features

- ⏰ **Scheduled Trigger**: Runs every Friday at 5:00 PM (configurable timezone)
- 📊 **GitHub Data Collection**: Fetches commits, closed issues, and merged PRs
- 🤖 **AI-Powered Summaries**: Uses Claude Sonnet 4 for engaging narrative reports
- 📬 **Multi-Channel Delivery**: Discord and Email notifications
- 🌐 **Multi-Language Support**: English (EN) and French (FR)

## Prerequisites

- n8n instance (self-hosted or n8n Cloud)
- GitHub Personal Access Token
- Anthropic API Key (for Claude AI)
- Discord Webhook URL (optional)
- SMTP credentials for email (optional)

## Installation (5 Steps)

### Step 1: Import the Workflow

1. Open your n8n instance
2. Navigate to **Workflows** → **Add Workflow** → **Import from File**
3. Upload `workflow.json` from this directory
4. The workflow will appear as "Weekly GitHub Summary Report"

### Step 2: Configure Environment Variables

Set up the following variables in n8n:

**Option A: Using n8n Environment Variables (Recommended)**
```bash
# In your n8n instance settings or .env file
GITHUB_REPO=your-username/your-repo
ANTHROPIC_API_KEY=sk-ant-xxxxx
LANGUAGE=EN  # or FR for French
```

**Option B: Using Workflow Variables**
1. Open the workflow editor
2. Click the **Variables** tab on the left sidebar
3. Set the following:
   - `GITHUB_REPO`: Your GitHub repository (format: `owner/repo`)
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
   - `LANGUAGE`: `EN` for English or `FR` for French

### Step 3: Set Up Credentials

Configure the following credentials in n8n:

1. **GitHub Token** (HTTP Header Auth)
   - Go to **Settings** → **Credentials** → **Add Credential**
   - Type: **Header Auth**
   - Name: `Authorization`
   - Value: `Bearer YOUR_GITHUB_TOKEN`
   - Create a token at: https://github.com/settings/tokens

2. **Anthropic API** (for Claude AI)
   - Type: **Anthropic API**
   - API Key: Your Anthropic API key
   - Get your key at: https://console.anthropic.com/

3. **Discord Webhook** (optional)
   - Type: **Discord Webhook**
   - Webhook URL: Your Discord channel webhook URL
   - Create webhook in Discord: Channel Settings → Integrations → Webhooks

4. **SMTP Email** (optional)
   - Type: **SMTP**
   - Configure your email provider settings
   - Update `toEmail` and `fromEmail` in the Email Notification node

### Step 4: Update Node Credentials

Link your credentials to each node:

1. Click on each GitHub node (Get Commits, Get Closed Issues, Get Merged PRs)
   - Select your **GitHub Token** credential

2. Click on **Claude AI Summary** node
   - Select your **Anthropic API** credential

3. Click on **Discord Notification** node
   - Select your **Discord Webhook** credential

4. Click on **Email Notification** node
   - Select your **SMTP** credential
   - Update recipient email address in parameters

### Step 5: Activate the Workflow

1. Click **Save** to save your workflow
2. Toggle the **Active** switch in the top-right corner
3. The workflow will now run every Friday at 5:00 PM

**To test immediately:**
- Click **Execute Workflow** button
- Or use **Execute Node** on the Schedule Trigger

## Workflow Diagram

```
┌─────────────────┐
│ Schedule Trigger│ (Friday 5PM)
│   (Cron: 0 17   │
│    * * 5)       │
└────────┬────────┘
         │
    ┌────┴────┬─────────────┐
    ▼         ▼             ▼
┌────────┐ ┌────────┐ ┌──────────┐
│ GitHub │ │ GitHub │ │  GitHub  │
│Commits │ │ Issues │ │   PRs    │
└────┬───┘ └────┬───┘ └────┬─────┘
     │          │          │
     ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌──────────┐
│Process │ │Process │ │ Filter   │
│Commits │ │ Issues │ │Merged PRs│
└────┬───┘ └────┬───┘ └────┬─────┘
     │          │          │
     └────┬─────┴──────────┘
          ▼
    ┌─────────────┐
    │ Combine Data│
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  Claude AI  │ (claude-sonnet-4-20250514)
    │   Summary   │
    └──────┬──────┘
           │
      ┌────┴────┐
      ▼         ▼
┌──────────┐ ┌──────────┐
│ Discord  │ │  Email   │
│Webhook   │ │Notif.    │
└──────────┘ └──────────┘
```

## Configuration Options

### Schedule Configuration

Edit the **Schedule Trigger** node to change the schedule:

```cron
0 17 * * 5    # Friday at 5:00 PM (default)
0 9 * * 1     # Monday at 9:00 AM
0 12 * * *    # Daily at noon
```

### Language Settings

Set the `LANGUAGE` variable to:
- `EN` - English summary (default)
- `FR` - French summary (Français)

### Customization

**Modify the Claude AI prompt:**
1. Open the **Claude AI Summary** node
2. Edit the `system` and `user` messages
3. Customize the summary format and style

**Adjust commit/issue lookback period:**
- Default: Last 7 days
- Modify in the Code nodes: `7 * 24 * 60 * 60 * 1000`

## Troubleshooting

### Common Issues

1. **No data returned from GitHub**
   - Verify your GitHub token has `repo` scope
   - Check `GITHUB_REPO` format: `owner/repo`
   - Ensure repository exists and has activity

2. **Claude API errors**
   - Verify API key is valid and has credits
   - Check API key format starts with `sk-ant-`
   - Ensure model `claude-sonnet-4-20250514` is available

3. **Discord notifications not working**
   - Verify webhook URL is correct
   - Test webhook URL in a browser
   - Check Discord server permissions

4. **Email not sending**
   - Verify SMTP credentials
   - Check sender and recipient email addresses
   - Review SMTP server logs

### Debug Mode

Enable debug logging in n8n:
```bash
export N8N_LOG_LEVEL=debug
n8n start
```

## File Structure

```
n8n-weekly-summary/
├── workflow.json    # n8n workflow definition
├── README.md        # This file
└── LICENSE          # MIT License
```

## API References

- [GitHub REST API](https://docs.github.com/en/rest)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)
- [n8n Documentation](https://docs.n8n.io)
- [n8n Schedule Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/)

## Support

For issues or feature requests:
- Open an issue in the GitHub repository
- Check n8n community: https://community.n8n.io

## License

MIT License - See LICENSE file for details.

---

Created by: zxy0314-work  
Version: 1.0.0  
Last Updated: 2026-01-20