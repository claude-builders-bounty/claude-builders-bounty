# n8n + Claude Weekly Dev Summary Workflow

Automated weekly development summary generator using n8n and Claude API.

## Features

- **Weekly Schedule**: Runs every Friday at 5pm (configurable)
- **GitHub Integration**: Fetches commits, closed issues, merged PRs
- **AI Summary**: Uses Claude API to generate narrative summary
- **Discord Delivery**: Sends summary to Discord webhook

## Installation

### 1. Import Workflow
1. Open n8n (https://n8n.io or your self-hosted instance)
2. Go to Settings > Imports
3. Upload `workflow.json`

### 2. Configure Variables
In n8n Variables, set:
- `GITHUB_REPO` = "owner/repo" (e.g., "claude-builders-bounty/claude-builders-bounty")
- `DISCORD_WEBHOOK_URL` = your Discord webhook URL

### 3. Add Credentials
- **GitHub**: No credentials needed for public repos (or add token for private)
- **Discord**: Webhook URL only
- **OpenAI/Claude**: Add your API key

## Setup (5 steps)

```bash
# 1. Clone this repo or download workflow.json
# 2. Import to n8n
# 3. Set GITHUB_REPO variable
# 4. Set DISCORD_WEBHOOK_URL variable
# 5. Activate workflow
```

## Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | GitHub repository | `owner/repo` |
| `DISCORD_WEBHOOK_URL` | Discord webhook | `https://discord.com/api/webhooks/...` |

## Output Example

```
**Weekly Dev Summary** | claude-builders-bounty/claude-builders-bounty

This week the team closed 12 issues and merged 8 PRs.
Key changes include the new PR Reviewer Agent and improvements
to the weekly summary workflow...

## Activity
- 23 commits pushed
- 12 issues closed
- 8 PRs merged
```

## Trigger Schedule

Default: Friday 5pm. Modify in "Weekly Schedule" node:
```javascript
{
  "triggerAtHour": 17,
  "triggerAtMinute": 0,
  "triggerOnWeekday": "FRIDAY"
}
```

## Testing

1. Click "Test Workflow" in n8n
2. Check Discord for summary
3. Verify GitHub data accuracy