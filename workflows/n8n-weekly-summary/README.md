# GitHub Weekly Summary n8n Workflow

> Automated weekly narrative summaries of GitHub repository activity powered by Claude AI

## Overview

This n8n workflow automatically generates weekly narrative summaries of GitHub repository activity using the Claude API. It fetches commits, closed issues, and merged PRs from the past week, then uses Claude to generate an engaging narrative summary delivered via email or Discord.

## Features

- ✅ **Weekly Cron Trigger**: Runs every Friday at 5 PM (configurable)
- ✅ **GitHub API Integration**: Fetches commits, issues, and PRs
- ✅ **Claude AI Summaries**: Uses `claude-sonnet-4-20250514` for narrative generation
- ✅ **Multiple Delivery Options**: Email and Discord webhook
- ✅ **Multi-language Support**: English and French
- ✅ **Fully Configurable**: Environment variables for easy setup

## Installation

### Step 1: Import Workflow

```bash
# Download the workflow
git clone https://github.com/ljapptest-art/n8n-weekly-summary.git

# In n8n, go to Workflows > Import from File
# Select n8n-workflow.json
```

### Step 2: Configure Credentials

1. **GitHub Token**: Create a Personal Access Token with `repo` scope
2. **Claude API**: Get your API key from [Anthropic Console](https://console.anthropic.com/)
3. **Email/Discord**: Configure either or both delivery methods

### Step 3: Set Environment Variables

```bash
GITHUB_REPO=owner/repo              # Target repository
GITHUB_TOKEN=ghp_xxx                # GitHub Personal Access Token
ANTHROPIC_API_KEY=sk-ant-xxx        # Claude API key
LANGUAGE=EN                         # EN or FR
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/xxx  # Optional
EMAIL_RECIPIENT=team@example.com    # Optional
```

### Step 4: Configure Credentials in n8n

1. Go to **Credentials** > **Add Credential**
2. Add **HTTP Header Auth** for GitHub (header: `Authorization`, value: `token YOUR_GITHUB_TOKEN`)
3. Add **Anthropic API** credential for Claude

### Step 5: Activate the Workflow

Click **Active** toggle in n8n to enable the workflow.

## Workflow Diagram

```
┌─────────────────┐
│  Weekly Trigger │ (Friday 5 PM)
│    (Cron)       │
└────────┬────────┘
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
┌───────┐ ┌───────┐   ┌─────────┐
│Commits│ │Issues │   │   PRs   │
└───┬───┘ └───┬───┘   └────┬────┘
    │         │            │
    └────┬────┴────────────┘
         ▼
┌─────────────────┐
│ Process Data    │
│ (Code Node)     │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Claude API      │
│ Generate Summary│
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌─────────┐
│ Email │ │ Discord │
└───────┘ └─────────┘
```

## Configuration Options

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GITHUB_REPO` | Yes | Repository in `owner/repo` format | - |
| `GITHUB_TOKEN` | Yes | GitHub Personal Access Token | - |
| `ANTHROPIC_API_KEY` | Yes | Claude API key | - |
| `LANGUAGE` | No | Summary language (`EN` or `FR`) | `EN` |
| `DISCORD_WEBHOOK_URL` | No | Discord webhook URL | - |
| `EMAIL_RECIPIENT` | No | Email recipient address | - |

### Cron Schedule

Default: `0 17 * * 5` (Friday at 5 PM)

To change, edit the Schedule Trigger node and modify the cron expression.

## Sample Output

### English

```markdown
# Weekly Summary: owner/repo

## Introduction

This week saw 23 commits, 5 issues closed, and 3 PRs merged in the owner/repo repository.

## Highlights

- Major feature: New authentication system
- Performance improvements in API routes
- Bug fixes in payment processing

## Technical Details

- Added JWT-based authentication (+450 lines)
- Refactored database queries for 40% speed improvement
- Fixed memory leak in background workers

## Next Steps

- Continue with OAuth integration
- Expand test coverage for new features
```

### French

```markdown
# Résumé hebdomadaire: owner/repo

## Introduction

Cette semaine a vu 23 commits, 5 issues fermées et 3 PRs fusionnées.

## Points forts

- Fonctionnalité majeure: Nouveau système d'authentification
- Améliorations de performance dans les routes API
- Corrections de bugs dans le traitement des paiements
```

## Testing

1. In n8n, open the workflow
2. Click **Execute Workflow** to test manually
3. Check the output of each node
4. Verify the summary is delivered to your chosen destination

## Troubleshooting

### GitHub API Errors

- Ensure `GITHUB_TOKEN` has `repo` scope
- Check repository exists and is accessible
- Verify rate limits haven't been exceeded

### Claude API Errors

- Verify `ANTHROPIC_API_KEY` is valid
- Check API rate limits
- Ensure model `claude-sonnet-4-20250514` is available

### Delivery Issues

**Email**: Check SMTP credentials and recipient address
**Discord**: Verify webhook URL is correct and active

## Requirements

- n8n version 1.0+
- GitHub Personal Access Token
- Anthropic API key
- SMTP server (for email) or Discord webhook

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Bounty

Created for [Claude Builders Bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) - $200
