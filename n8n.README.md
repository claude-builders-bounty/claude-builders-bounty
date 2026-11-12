# Weekly GitHub Dev Summary — n8n + Claude Code workflow

An n8n workflow that automatically generates a weekly narrative summary of a
GitHub repo's activity using the Claude API, delivered to a Discord/Slack webhook.

## Features
- **Trigger**: weekly cron (Friday 5pm, `0 17 * * 5`)
- **Fetches** from GitHub API: commits, closed issues, merged PRs (past 7 days)
- **Calls** Claude API (`claude-sonnet-4-20250514`) to write the narrative
- **Delivers** via Discord/Slack webhook
- **Configurable**: repo, language (EN/FR), destination webhook — all via variables

## Setup (3 steps)
1. Import `weekly-dev-summary.json` in n8n (**Workflows → Import from File**).
2. Add two credentials:
   - **Header Auth** for GitHub (`Authorization: Bearer <GITHUB_TOKEN>`, or use
     `X-GitHub-Api-Version` for public repos)
   - **Header Auth** for Claude (`x-api-key: <ANTHROPIC_API_KEY>`)
3. Set the workflow's variables: `repo` (e.g. `owner/repo`), `lang` (`EN`/`FR`),
   and the destination `webhookUrl`.

## How it works
```
Cron (Fri 5pm)
  ├─ Fetch Commits (GitHub API)
  ├─ Fetch Closed Issues
  └─ Fetch Merged PRs
        → Build Prompt (aggregate into one text)
              → Call Claude API (narrative summary)
                    → Deliver (Discord/Slack webhook)
```

## Test
Executed against a live n8n instance; the trigger fires, the three GitHub fetches
return 200, the prompt is built, and the Claude call returns a narrative summary
which posts to the webhook.
