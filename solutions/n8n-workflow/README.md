# Weekly Dev Summary with Claude - n8n Workflow

Automatically generate a weekly narrative summary of GitHub repository activity using the Claude API and n8n.

## Features

- ✅ Weekly cron trigger (Friday at 5pm)
- ✅ Fetches commits, closed issues, and merged PRs from GitHub API
- ✅ Generates narrative summary using Claude API (`claude-sonnet-4-20250514`)
- ✅ Delivers summary via email or Discord/Slack webhook
- ✅ Configurable variables: GitHub repo, destination, language (EN/FR)

## Installation

### Step 1: Import Workflow

```bash
# In n8n, go to Workflows → Import from File
# Select weekly-dev-summary.json
```

Or import via URL:
```bash
n8n import:workflow --input=https://raw.githubusercontent.com/your-repo/weekly-dev-summary.json
```

### Step 2: Configure Credentials

1. **GitHub Token**
   - Go to Credentials → Add Credential → HTTP Header Auth
   - Name: `GitHub Token`
   - Header Name: `Authorization`
   - Header Value: `Bearer YOUR_GITHUB_TOKEN`

2. **Anthropic API Key**
   - Go to Credentials → Add Credential → HTTP Header Auth
   - Name: `Anthropic API Key`
   - Header Name: `x-api-key`
   - Header Value: `YOUR_ANTHROPIC_API_KEY`

### Step 3: Set Environment Variables

In n8n Settings → Variables, add:

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `GITHUB_REPO` | `owner/repo` | GitHub repository |
| `SUMMARY_LANGUAGE` | `EN` or `FR` | Output language |
| `NOTIFICATION_EMAIL` | `team@example.com` | Email recipient (optional) |
| `WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Discord/Slack webhook |

### Step 4: Activate Workflow

Click "Active" toggle in n8n to enable the weekly schedule.

## Setup Instructions (5 Steps)

1. Import `weekly-dev-summary.json` into n8n
2. Add GitHub HTTP Header Auth credential with your token
3. Add Anthropic HTTP Header Auth credential with your API key
4. Set environment variables for repo and webhook
5. Activate the workflow

## Output Format

The workflow generates Markdown summaries like:

```markdown
## Weekly Development Summary - owner/repo
**Week: May 13 - May 20, 2026**

### Highlights
This week we made significant progress on the authentication module.
The team merged 5 PRs addressing user feedback and closed 8 issues.

### Top Contributors
- Alice Chen (12 commits)
- Bob Smith (8 commits)
- Carol Jones (5 commits)

### Key Changes
- PR #123: Implemented OAuth2 support
- Issue #98: Fixed login timeout bug
- Commit: Refactored session management

Thanks to all contributors this week! 🎉
```

## Configuration Options

### Schedule

Edit the cron expression in the Schedule Trigger node:
- `0 17 * * 5` - Friday at 5pm
- `0 9 * * 1` - Monday at 9am
- `0 12 * * *` - Daily at noon

### Language

Set `SUMMARY_LANGUAGE` environment variable:
- `EN` - English output
- `FR` - French output

### Delivery

Choose one or both delivery methods:
- Email: Set `NOTIFICATION_EMAIL` variable
- Webhook: Set `WEBHOOK_URL` variable (Discord or Slack)

## Testing

### Manual Test

```bash
# In n8n, click "Execute Workflow" button
# Check output in "Extract Summary" node
```

### Test with Sample Data

```bash
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4-20250514", "max_tokens": 1024, "messages": [{"role": "user", "content": "Test summary"}]}'
```

## Screenshots

See `screenshots/` folder for:
- `workflow-execution.png` - Successful workflow run
- `sample-output.png` - Generated summary example

## Troubleshooting

| Issue | Solution |
|-------|----------|
| GitHub API rate limit | Use authenticated requests (increases limit to 5000/hour) |
| Claude API timeout | Reduce max_tokens or check API status |
| Webhook not received | Verify webhook URL and check Discord/Slack settings |
| Empty summary | Check GITHUB_REPO variable format (must be `owner/repo`) |

## Resources

- n8n docs: https://docs.n8n.io
- Claude API docs: https://docs.anthropic.com
- GitHub API docs: https://docs.github.com/rest

## License

MIT