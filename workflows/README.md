# n8n + Claude: Automated GitHub Weekly Report

> Generates a narrative weekly development summary for any GitHub repository using the Claude API and delivers it to Discord (or Slack).

## What It Does

Every Friday at 5 PM, this n8n workflow:

1. **Fetches** the last 7 days of activity from a GitHub repo (commits, closed issues, merged PRs)
2. **Sends** the data to Claude API (claude-sonnet-4-20250514) for intelligent summarization
3. **Delivers** a polished weekly report to your Discord/Slack channel

## Setup (5 Steps)

### Step 1: Import the Workflow

Open your n8n instance -> Workflows -> Import from File -> select github-weekly-report.json

### Step 2: Create GitHub Credential

Go to Settings -> Credentials -> Add Credential -> Header Auth:
- Name: GitHub Token
- Header Name: Authorization
- Header Value: token ghp_YOUR_GITHUB_TOKEN

### Step 3: Configure Variables

Open the **Config Variables** node and set:

- **OWNER** - GitHub repo owner (e.g. anthropics)
- **REPO** - GitHub repo name (e.g. anthropic-sdk-python)
- **LANGUAGE** - Report language: English or French
- **WEBHOOK_URL** - Discord webhook URL
- **CLAUDE_API_KEY** - Your Anthropic API key (sk-ant-...)
- **GITHUB_TOKEN** - GitHub personal access token (ghp_...)

### Step 4: Test Execution

- Click Execute Workflow to test manually
- Verify the report appears in your Discord channel

### Step 5: Activate

Toggle the workflow to Active - it will run automatically every Friday at 5 PM.

## Workflow Architecture

Weekly Trigger (Friday 5pm)
  -> Config Variables (repo, keys, language)
    -> [parallel] Fetch Commits (GitHub API)
    -> [parallel] Fetch Closed Issues (GitHub API)
    -> [parallel] Fetch Merged PRs (GitHub API)
      -> Merge and Format Data (Code node)
        -> Generate Report with Claude API
          -> Extract and Split Report (handles Discord 2000-char limit)
            -> Send to Discord Webhook

## Customization

- **Change schedule**: Edit the cron expression in the trigger node (0 17 * * 5 = Friday 5pm)
- **Switch to Slack**: Change webhook body format to match Slack API
- **Change model**: Edit the model field (e.g. claude-opus-4-20250514)
- **Add email delivery**: Add an n8n Email node after report extraction

## Requirements

- n8n v1.0+ (self-hosted or cloud)
- GitHub Personal Access Token (with repo scope)
- Anthropic API Key
- Discord Webhook URL (or Slack incoming webhook)

## License

MIT
