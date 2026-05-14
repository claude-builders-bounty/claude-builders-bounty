# n8n Weekly Dev Summary Workflow

**Bounty:** #5 — $200 (Opire)

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API.

## Features

- **Weekly schedule** — runs every Friday at 5 PM (configurable)
- **Fetches from GitHub API**: commits, closed issues, merged PRs for the past 7 days
- **Calls Claude API** (`claude-sonnet-4-20250514`) to generate a narrative summary
- **Delivers via Slack** webhook with formatted message
- **Configurable**: repo name, destination channel, and language

## Installation (5 steps)

### 1. Import the workflow
1. Open n8n
2. Go to **Workflows** → **Add Workflow** → **Import from File**
3. Select `n8n-weekly-dev-summary.json`

### 2. Configure Claude API credentials
1. In n8n, go to **Credentials** → **Add Credential**
2. Type: **Claude API** (or create a "Header Auth" credential)
3. Add your Anthropic API key
4. Name it `claudeApi`

### 3. Configure GitHub repo (optional)
Edit the **Fetch GitHub Data** Code node:
```javascript
// Change these two lines at the top:
const repoOwner = 'your-org';
const repoName = 'your-repo';
```

### 4. Configure Slack
1. Add a Slack credential in n8n
2. Edit the **Send to Slack** node to set your channel

### 5. Activate
Click **Active** toggle to enable the weekly schedule.

## Workflow Structure

```
Schedule Trigger (Friday 5PM)
  ↓
Code Node: Fetch GitHub Data (commits, issues, PRs)
  ↓
Code Node: Format data for Claude API
  ↓
HTTP Request: Call Claude API (claude-sonnet-4-20250514)
  ↓
Code Node: Parse Claude response
  ↓
Slack: Send summary to channel
```

## Configuration Variables

| Variable | Location | Default |
|----------|----------|---------|
| GitHub Owner | Code node line 9 | `claude-builders-bounty` |
| GitHub Repo | Code node line 10 | `claude-builders-bounty` |
| GitHub Token | Code node line 11 | `''` (public repos) |
| Cron Schedule | Schedule Trigger | `0 17 * * 5` (Fri 5PM) |
| Slack Channel | Slack node | `general` |
| Claude Model | Format node | `claude-sonnet-4-20250514` |
| Language | Prompt in Format node | English |

## Output Format

The Slack message contains:
1. A narrative summary (2-3 paragraphs)
2. Key highlights and achievements
3. Areas needing attention
4. Overall project health assessment

## Requirements

- n8n v1.0+
- Claude API key (Anthropic)
- GitHub API access (for private repos, a token with `repo` scope)

## Testing

Click **Execute Workflow** in n8n to trigger a manual run. Verify:
1. GitHub data is fetched correctly
2. Claude API returns a summary
3. Slack message is delivered
