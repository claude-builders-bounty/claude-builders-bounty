# Weekly GitHub Development Summary

This n8n workflow sends a weekly GitHub development summary to Slack using the Claude API.

The workflow runs every Friday at 5 PM, reads the previous seven days of GitHub commits, closed issues, and merged pull requests, asks Claude to summarize the work, and posts the result to a Slack incoming webhook.

## Files

- `weekly-dev-summary.json` - importable n8n workflow export.

## Requirements

- n8n 1.x
- GitHub personal access token with read access to the target repository
- Anthropic API key
- Slack incoming webhook URL

## Configuration

Set these environment variables in the n8n runtime before activating the workflow:

| Variable | Required | Description |
|---|---:|---|
| `GITHUB_OWNER` | Yes | Repository owner or organization, for example `anthropics` |
| `GITHUB_REPO` | Yes | Repository name, for example `claude-code` |
| `GITHUB_TOKEN` | Yes | GitHub token used for API reads |
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `SLACK_WEBHOOK_URL` | Yes | Slack incoming webhook URL |
| `SUMMARY_LANGUAGE` | No | Output language: `EN` or `FR`. Defaults to `EN` |
| `CLAUDE_MODEL` | No | Claude model. Defaults to `claude-sonnet-4-20250514` |
| `SLACK_CHANNEL` | No | Optional channel override. Some Slack webhooks ignore this value |

## Setup

1. Set `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `SLACK_WEBHOOK_URL`, and optionally `SUMMARY_LANGUAGE=EN` or `SUMMARY_LANGUAGE=FR`.
2. Import `workflows/weekly-dev-summary.json` in n8n with **Workflows > Import from File**.
3. Execute the workflow manually once to verify GitHub, Claude, and Slack access.
4. Confirm the Slack message arrives in the configured destination channel.
5. Activate the workflow.

## Local n8n example

```bash
export GITHUB_OWNER=your-org
export GITHUB_REPO=your-repo
export GITHUB_TOKEN=ghp_your_token
export ANTHROPIC_API_KEY=sk-ant-your_key
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
export SUMMARY_LANGUAGE=EN
npx n8n
```

On Windows PowerShell:

```powershell
$env:GITHUB_OWNER = "your-org"
$env:GITHUB_REPO = "your-repo"
$env:GITHUB_TOKEN = "ghp_your_token"
$env:ANTHROPIC_API_KEY = "sk-ant-your_key"
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."
$env:SUMMARY_LANGUAGE = "EN"
npx n8n
```

## How It Works

The GitHub HTTP Request nodes fetch commits, closed issues, and closed pull requests. The **Build Claude Request** code node:

1. Calculates the last seven days.
2. Removes unmerged pull requests from the weekly PR list.
3. Removes pull requests from the closed issue list.
4. Sends the compact GitHub activity data to Claude.
5. Builds a Slack Block Kit payload.

The **Send to Slack** HTTP Request node posts the generated payload to the configured Slack webhook.

## Troubleshooting

- `Set GITHUB_OWNER and GITHUB_REPO before running this workflow.` - one or both repository variables are missing.
- `GitHub API 401` - check `GITHUB_TOKEN`.
- `Claude API 401` - check `ANTHROPIC_API_KEY`.
- `Slack webhook` errors - verify that `SLACK_WEBHOOK_URL` is an incoming webhook URL for the destination workspace.
- Empty summaries usually mean the target repository had little activity in the last seven days.

## Notes

- The workflow keeps the GitHub payload compact to avoid sending unnecessary data to Claude.
- The prompt tells Claude not to invent facts beyond the GitHub data.
- Slack section blocks have length limits, so the message is truncated if the generated summary is too long.
