# Weekly Dev Summary Workflow for n8n

An automated n8n workflow that generates weekly development summaries using Claude API and delivers them via Email, Discord, or Slack.

## 💰 Bounty

This workflow was created for [Claude Builders Bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) - $200

## Features

- ⏰ **Weekly Automation**: Runs every Friday at 5 PM
- 📊 **GitHub Integration**: Fetches commits, closed issues, and merged PRs
- 🤖 **AI-Powered**: Uses Claude API to generate narrative summaries
- 📧 **Multi-Channel Delivery**: Email, Discord, or Slack
- 🌍 **Multi-Language**: Supports English (EN) and French (FR)
- ⚙️ **Fully Configurable**: Environment variables for all settings

## Prerequisites

- n8n instance (cloud or self-hosted)
- GitHub Personal Access Token
- Claude API Key
- Email/SMTP credentials OR Discord/Slack webhook

## Setup Instructions

### Step 1: Import the Workflow

1. Download `weekly-dev-summary-claude.json`
2. In n8n, go to **Workflows** → **Import from File**
3. Select the downloaded JSON file

### Step 2: Configure Environment Variables

In n8n, go to **Settings** → **Variables** and add:

```bash
# Required
GITHUB_OWNER=your-github-username
GITHUB_REPO=your-repository-name
GITHUB_TOKEN=ghp_your_github_token
CLAUDE_API_KEY=sk-ant-your-claude-api-key

# Delivery Configuration
DESTINATION_TYPE=email          # Options: email, discord, slack
DESTINATION_VALUE=recipient@example.com  # Email, webhook URL, or channel ID

# Optional
LANGUAGE=EN                     # Options: EN, FR (default: EN)
```

### Step 3: Configure Credentials

#### For Email Delivery:
1. Go to **Settings** → **Credentials**
2. Add **SMTP** credentials
3. Configure your email provider settings

#### For Discord Delivery:
- Set `DESTINATION_TYPE=discord`
- Set `DESTINATION_VALUE` to your Discord webhook URL

#### For Slack Delivery:
1. Go to **Settings** → **Credentials**
2. Add **Slack API** credentials
3. Set `DESTINATION_TYPE=slack`
4. Set `DESTINATION_VALUE` to your channel ID (e.g., `#general`)

### Step 4: Test the Workflow

1. Click **Execute Workflow** to test manually
2. Check the execution results
3. Verify the summary is delivered to your configured destination

### Step 5: Activate

1. Toggle the workflow to **Active**
2. The workflow will run automatically every Friday at 5 PM

## How It Works

```
Weekly Trigger (Friday 5PM)
    ↓
Set Date Range (Last 7 days)
    ↓
Fetch GitHub Data
├── Commits
├── Closed Issues
└── Merged PRs
    ↓
Aggregate & Format Data
    ↓
Call Claude API (Generate Summary)
    ↓
Extract Summary
    ↓
Route by Destination
├── Email (SMTP)
├── Discord (Webhook)
└── Slack (API)
```

## Workflow Nodes

| Node | Purpose |
|------|---------|
| Weekly Trigger | Cron schedule - every Friday at 5 PM |
| Set Date Range | Calculate last week's date range |
| Fetch Commits | Get commits from GitHub API |
| Fetch Closed Issues | Get closed issues from GitHub API |
| Fetch PRs | Get merged PRs from GitHub API |
| Aggregate Data | Combine and format GitHub data |
| Call Claude API | Generate narrative summary using AI |
| Extract Summary | Parse Claude's response |
| Route by Destination | Determine delivery channel |
| Send Email/Send to Discord/Send to Slack | Deliver the summary |

## Sample Output

```markdown
# Weekly Development Summary - owner/repo

**Period:** May 12 - May 19, 2026

## Statistics
- **Commits:** 23
- **Closed Issues:** 5
- **Merged PRs:** 4

## Highlights

### Recent Commits
- feat: add user authentication (john-doe)
- fix: resolve memory leak in parser (jane-smith)
- docs: update API documentation (bob-wilson)

### Closed Issues
- #42: Fix null pointer exception
- #37: Add retry logic for API calls

### Merged Pull Requests
- #45: Implement caching layer by @john-doe
- #44: Update dependencies by @jane-smith

---
*Generated automatically by n8n + Claude*
```

## Testing

The workflow has been tested on:
- n8n Cloud (v1.x)
- n8n Self-hosted (Docker)

Test execution screenshot: [See execution log in n8n]

## Customization

### Change Schedule
Edit the **Weekly Trigger** node to modify:
- Day of week
- Time of day
- Frequency

### Modify Summary Format
Edit the **Call Claude API** node to customize:
- System prompt
- User prompt
- Max tokens

### Add More Data Sources
Add additional HTTP Request nodes to fetch:
- GitHub Discussions
- GitHub Releases
- External metrics

## Troubleshooting

### Workflow Not Triggering
- Check if workflow is **Active**
- Verify trigger schedule settings
- Check n8n execution logs

### GitHub API Errors
- Verify `GITHUB_TOKEN` has `repo` scope
- Check rate limits: https://api.github.com/rate_limit

### Claude API Errors
- Verify `CLAUDE_API_KEY` is valid
- Check API usage limits in Anthropic console

### Delivery Failures
- Verify destination credentials
- Check spam folders for emails
- Verify webhook URLs are correct

## License

MIT - Created for Claude Builders Bounty

## Credits

- Workflow: Created by 1150654748m-dev
- AI: Claude by Anthropic
- Platform: n8n
