# n8n Weekly Dev Summary Workflow

An n8n workflow that automatically generates weekly narrative summaries of GitHub repository activity using the Claude API.

## 💰 Bounty

This project was created for the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) - $200 reward.

## Features

- ✅ Weekly cron trigger (Fridays at 5pm)
- ✅ Fetches from GitHub API:
  - Commits from the past week
  - Closed issues
  - Merged PRs
- ✅ Calls Claude API (`claude-sonnet-4-20250514`) to generate narrative summary
- ✅ Delivers summary via:
  - Email OR
  - Slack webhook
- ✅ Configurable variables:
  - GitHub repo
  - Destination channel
  - Language (EN/FR)

## Prerequisites

- n8n instance (cloud or self-hosted)
- GitHub token (for private repos)
- Anthropic API key
- Email SMTP credentials OR Slack webhook

## Setup (5 Steps)

### Step 1: Import Workflow
1. Open your n8n instance
2. Click "Add Workflow"
3. Select "Import from File"
4. Upload `weekly-dev-summary.json`

### Step 2: Configure Credentials
Create these credentials in n8n:
- **GitHub API** (if accessing private repos)
- **Anthropic** (Claude API key)
- **Slack** OR **SMTP** (for delivery)

### Step 3: Set Environment Variables
In n8n Settings → Variables:
```
GITHUB_OWNER=your-github-username
GITHUB_REPO=your-repo-name
LANGUAGE=EN
DESTINATION_CHANNEL=#dev-updates
EMAIL_RECIPIENTS=team@example.com
```

### Step 4: Configure Trigger
Edit the "Weekly Trigger" node:
- Default: Every Friday at 5:00 PM
- Adjust timezone as needed

### Step 5: Activate
Click "Active" toggle to enable the workflow.

## Workflow Overview

```
Weekly Trigger (Cron)
    ↓
Fetch Commits → Fetch Closed Issues → Fetch Merged PRs
    ↓
Filter Recent PRs (last 7 days)
    ↓
Generate Summary (Claude API)
    ↓
Send to Slack + Send Email
```

## Testing

### Manual Test
1. Click "Execute Workflow"
2. Check execution results
3. Verify summary is generated
4. Check delivery (Slack/Email)

### Screenshot
Include a screenshot of successful execution in your PR.

## Sample Output

```markdown
📊 Weekly Dev Summary - myproject

This week saw 15 commits, 3 closed issues, and 2 merged PRs. 
The team focused on improving API performance and fixing critical bugs.

Key Highlights:
• Reduced API response time by 40%
• Fixed authentication edge case
• Added new dashboard widgets

Notable Contributions:
• @alice: Performance optimization (#123)
• @bob: Bug fix for login flow (#124)

Coming Next Week:
• Mobile app integration
• Database migration
```

## Customization

### Change Schedule
Edit "Weekly Trigger" node:
- Field: `rule.interval`
- Options: weeks, days, hours

### Change Language
Set `LANGUAGE` variable:
- `EN` - English
- `FR` - French

### Add More Data Sources
Add additional HTTP Request nodes to fetch:
- GitHub releases
- GitHub discussions
- External metrics

## Troubleshooting

### No data fetched
- Check GitHub token permissions
- Verify repo name is correct
- Check if repo has recent activity

### Claude API errors
- Verify Anthropic API key
- Check rate limits
- Review prompt in "Generate Summary" node

### Delivery failures
- Verify Slack webhook URL
- Check SMTP credentials
- Confirm destination channel exists

## Files

- `weekly-dev-summary.json` - n8n workflow (import this)
- `README.md` - This file

## License

MIT
