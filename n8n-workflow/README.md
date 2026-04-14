# n8n Weekly GitHub Dev Summary (Claude)

Automatically generates a weekly narrative summary of your GitHub repo's activity using the Claude API.

## Features

- **Weekly cron trigger** (Friday 5pm, configurable)
- **Fetches** commits, closed issues, and merged PRs from GitHub API
- **Generates** a narrative summary using Claude (`claude-sonnet-4-20250514`)
- **Delivers** via Discord or Slack webhook
- **Configurable** repo, webhook URL, and language (EN/FR)

## Setup (5 steps)

1. **Import the workflow** into n8n: Settings → Import from File → select `weekly-github-summary.json`

2. **Set environment variables** in n8n:
   - `GITHUB_TOKEN` — GitHub personal access token with `repo` scope
   - `CLAUDE_API_KEY` — Anthropic API key

3. **Configure the workflow variables** (first Code node):
   - `repo`: `owner/repo-name` (e.g., `facebook/react`)
   - `webhookUrl`: Your Discord or Slack webhook URL
   - `language`: `EN` or `FR` (default: EN)

4. **Set the schedule**: Edit the Schedule Trigger node to your preferred day/time

5. **Activate** the workflow and test with "Execute Workflow"

## How It Works

```
Weekly Trigger → Fetch Commits → Fetch Issues → Fetch PRs → Format → Claude API → Webhook
```

The workflow runs every Friday at 5pm (configurable), pulls the week's activity from GitHub, sends it to Claude for a narrative summary, and posts the result to your team channel.

## Example Output

```
📊 **Weekly Dev Summary — my-org/my-repo**
📅 Week of April 7-14, 2026

This week saw 12 commits across 3 contributors. The team focused on authentication improvements and bug fixes.

**Key achievements:**
- Migrated auth flow to session-based approach (@alice, 4 commits)
- Fixed critical memory leak in data pipeline (@bob, #234)
- Added CSV export feature for reports (@charlie, #241)

**Closed:** 5 issues | **Merged:** 3 PRs

Great work team! 🚀
```

## Customization

- Change the trigger schedule in the Schedule Trigger node
- Modify the Claude prompt in the HTTP Request node body
- Add email delivery by appending an Email node after the webhook
