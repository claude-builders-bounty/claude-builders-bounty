# GitHub Weekly Summary with Claude - n8n Workflow

## Overview

This n8n workflow automatically generates a **weekly narrative summary** of GitHub repository activity using the Claude API.

## Features

- 📅 **Weekly Schedule**: Runs every Monday at 9:00 AM
- 🐙 **GitHub Integration**: Fetches issues, PRs, and commits from the past 7 days
- 🤖 **AI-Powered**: Uses Claude Sonnet 4 to generate engaging narrative summaries
- 📝 **Professional Output**: Creates team-ready reports highlighting achievements and trends

## Workflow Structure

```
Schedule Trigger (Weekly)
    ├── GitHub Issues (past 7 days)
    ├── GitHub Pull Requests (past 7 days)
    └── GitHub Commits (past 7 days)
            ↓
        Merge Data
            ↓
      Claude API (Generate Summary)
            ↓
      Format Output
```

## Setup Instructions

### 1. Import the Workflow

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `github-weekly-summary.json`

### 2. Configure Credentials

#### GitHub API Credentials
- Go to **Credentials** → **Add Credential** → **GitHub API**
- Generate a personal access token at: https://github.com/settings/tokens
- Required scopes: `repo`, `read:user`
- Enter your token in the credential setup

#### Claude API Credentials
- Go to **Credentials** → **Add Credential** → **HTTP Header Auth**
- Name: `Claude API`
- Header Name: `x-api-key`
- Header Value: Your Anthropic API key (get from https://console.anthropic.com)

### 3. Set Environment Variables

Create a `.env` file in your n8n directory or set these variables:

```bash
GITHUB_REPO_OWNER=claude-builders-bounty
GITHUB_REPO_NAME=claude-builders-bounty
CLAUDE_API_KEY=your_anthropic_api_key_here
```

### 4. Activate the Workflow

1. Open the workflow in n8n editor
2. Click **Activate** toggle (top right)
3. The workflow will run every Monday at 9:00 AM

## Output Format

The workflow generates a summary with:

```markdown
# Weekly Development Summary
**Repository:** claude-builders-bounty/claude-builders-bounty
**Period:** 2026-04-14 to 2026-04-21

## 🎯 Key Achievements
- Major features shipped
- Critical bugs fixed
- Milestone reached

## 📊 Activity Overview
- Issues: X opened, Y closed
- PRs: Merged, In Review
- Commits: By contributor

## 🔥 Trends & Patterns
- ...

## ⚠️ Blockers & Concerns
- ...

## 👏 Team Highlights
- Shoutouts to contributors
```

## Customization

### Change Schedule
Edit the **Schedule Trigger** node:
- Change `days` to `1` for daily summaries
- Add `hours` and `minutes` for specific times

### Modify Claude Prompt
Edit the **Claude API** node's system message to adjust:
- Tone (more casual/formal)
- Focus areas (technical details vs. business impact)
- Output format (markdown, plain text, HTML)

### Add Output Destinations
Add nodes after **Format Output**:
- **Slack**: Send to team channel
- **Email**: Email to stakeholders
- **Notion**: Save to wiki
- **GitHub Issue**: Create weekly summary issue

## Testing

### Manual Test
1. Click **Execute Workflow** button in n8n editor
2. Check each node's output
3. Verify Claude API response

### Test with Sample Data
1. Use **pinData** feature in n8n
2. Add sample issues/PRs/commits
3. Run workflow without hitting GitHub API

## Troubleshooting

### GitHub API Rate Limits
- Use GitHub App credentials for higher limits
- Add error handling for 403 responses

### Claude API Errors
- Verify API key is valid
- Check token limits (max_tokens: 4096)
- Ensure anthropic-version header is set

### Workflow Not Triggering
- Check workflow is **Active**
- Verify n8n instance is running
- Check timezone settings

## Cost Estimation

- **GitHub API**: Free (within rate limits)
- **Claude API**: ~$0.02-0.05 per summary (depending on repo size)
- **Monthly Cost**: ~$0.10-0.20 for weekly summaries

## Bounty Information

This workflow resolves **Issue #5** ($200 Bounty) from claude-builders-bounty.

**Acceptance Criteria Met:**
- ✅ Complete n8n workflow in `.json` format
- ✅ Uses `claude-sonnet-4-20250514` model
- ✅ Automated weekly GitHub activity summary
- ✅ Narrative format suitable for team sharing

## License

MIT License - See repository LICENSE
