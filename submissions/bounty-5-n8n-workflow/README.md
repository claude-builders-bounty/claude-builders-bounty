# GitHub Weekly Dev Summary — n8n Workflow

Automatically generates a narrative weekly summary of any GitHub repo's activity using the Claude API, then delivers it to a Discord channel (or Slack — see Variables).

Triggers every **Friday at 5pm** via cron.

## Setup (5 steps)

**1. Import the workflow**

In n8n: Workflows → Import from File → select `github-weekly-summary.workflow.json`

**2. Set your variables**

In n8n Settings → Variables, create:

| Variable | Value | Required |
|----------|-------|----------|
| `GITHUB_REPO` | `owner/repo` (e.g. `anthropics/claude-code`) | Yes |
| `GITHUB_TOKEN` | Your GitHub PAT (`repo` scope) | Yes |
| `ANTHROPIC_API_KEY` | Your Claude API key (`sk-ant-...`) | Yes |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for your channel | Yes |
| `LANGUAGE` | `EN` or `FR` | Optional (default: `EN`) |

**3. Activate the workflow**

Toggle the workflow to Active. It will run automatically every Friday at 5pm.

**4. Test it manually**

Click "Execute Workflow" on the trigger node to run it immediately and verify the Discord message arrives.

**5. Done**

You'll receive a weekly summary like this every Friday in your Discord channel.

---

## What it fetches from GitHub

- Last 7 days of commits (up to 50)
- Closed issues this week (up to 20)
- Merged PRs this week (up to 20)

## What Claude generates

A 3-4 paragraph narrative summary in plain text:
1. Overall theme of the week
2. Highlights (key commits, shipped features, closed bugs)
3. What's coming / in progress

## Discord output example

> **📊 Weekly Dev Summary — anthropics/claude-code**
>
> This week was defined by stability and developer experience improvements. The team shipped 23 commits focused primarily on fixing edge cases in the hook system and improving error messages across the board.
>
> Highlights include the merge of the long-awaited voice input fix (#412), three documentation PRs that clarified the CLAUDE.md spec, and the closure of 8 open issues dating back to February. The pre-tool-use hook refactor landed cleanly with no regressions.
>
> Looking ahead, two open PRs are in review targeting performance improvements to the diff renderer. Expect those to land early next week.
>
> *Saturday, March 29, 2026 · Powered by Claude*

## Slack variant

Replace the "Post to Discord" node with an HTTP Request to your Slack webhook URL:

```json
{
  "text": "📊 *Weekly Dev Summary — {{repo}}*\n\n{{summary}}"
}
```

## Requirements

- n8n v1.0+ (self-hosted or cloud)
- GitHub account with PAT
- Anthropic API key
- Discord server with a webhook URL (free)
