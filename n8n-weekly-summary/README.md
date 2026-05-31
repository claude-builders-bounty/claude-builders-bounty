# n8n Weekly Dev Summary

Automated weekly summary of GitHub repository activity using n8n and Claude API.

## Features

- Weekly cron trigger (configurable)
- Fetches commits, closed issues, and merged PRs
- Generates narrative summary using Claude API
- Delivers via email
- Configurable: repo, language, destination

## Setup (5 steps)

1. **Import workflow**: In n8n, go to Workflows → Import from File → Select `github-weekly-summary.json`

2. **Configure credentials**:
   - GitHub: Add your GitHub API token
   - SMTP: Add your email SMTP settings
   - Claude API: Add your Anthropic API key as HTTP header

3. **Set environment variables**: Copy `.env.example` to `.env` and fill in:
   ```bash
   GITHUB_OWNER=your-org
   GITHUB_REPO=your-repo
   FROM_EMAIL=noreply@yourdomain.com
   TO_EMAIL=team@yourdomain.com
   LANGUAGE=English  # or French, etc.
   ```

4. **Activate workflow**: Toggle the workflow to "Active" in n8n

5. **Test**: Click "Execute Workflow" to test manually

## Workflow Overview

```
Weekly Trigger (Cron)
    ↓
Fetch Commits → Fetch Issues → Fetch PRs
    ↓
Aggregate Data
    ↓
Generate Summary (Claude API)
    ↓
Send Email
```

## Requirements

- n8n instance (cloud or self-hosted)
- GitHub API token
- Anthropic API key
- SMTP credentials

## Customization

- Change cron schedule in "Weekly Trigger" node
- Switch to Discord/Slack by replacing "Send Email" node
- Modify Claude prompt in "Generate Summary" node