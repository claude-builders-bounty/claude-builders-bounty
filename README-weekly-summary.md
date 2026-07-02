# Weekly Dev Summary — n8n + Claude Workflow

**Bounty:** [#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) — $200

An n8n workflow that automatically generates a narrative weekly summary of a GitHub repo's activity using the Claude API.

## How to Set Up

### Step 1: Import the Workflow
1. Open your n8n instance (self-hosted or n8n.cloud)
2. Go to **Workflows** → **Import from File**
3. Select `weekly-dev-summary.json`

### Step 2: Configure Credentials
Create these credentials in n8n:

| Credential | Type | What to enter |
|---|---|---|
| GitHub Token | HTTP Header Auth | `Authorization: Bearer <your_github_pat>` |
| Anthropic API Key | HTTP Header Auth | `x-api-key: <your_claude_api_key>` |

### Step 3: Set Variables
Configure these workflow-level variables in n8n:

| Variable | Example | Description |
|---|---|---|
| `REPO_OWNER` | `vercel` | GitHub organization or username |
| `REPO_NAME` | `next.js` | Repository name |
| `LANG` | `EN` or `FR` | Language for the summary |
| `WEBHOOK_URL` | (optional) | Discord/Slack/email webhook URL for delivery |

### Step 4: Activate
Toggle the workflow to **Active**. It will run every Friday at 5 PM.

### Step 5: Test
Click **Execute Workflow** to run a manual test. A successful run produces a formatted narrative summary.

## What It Does

1. **Weekly trigger** — Cron job fires every Friday at 5 PM
2. **Fetches data** — Gets commits, closed issues, and merged PRs from the past week via GitHub API
3. **Builds prompt** — Formats the data into a structured prompt for Claude
4. **Generates summary** — Calls `claude-sonnet-4-20250514` to produce a 3-4 paragraph narrative summary
5. **Delivers** — Sends the formatted summary to your webhook (Discord, Slack, email, etc.)

## Workflow Structure

```
Schedule Trigger → Calculate Dates
                    ↓        ↓        ↓
                 Commits   Issues    PRs
                    ↓        ↓        ↓
                    Build Prompt
                        ↓
                   Claude API
                        ↓
                  Format Output
                        ↓
                 Send to Webhook
```

## Screenshot

(Add a screenshot of a successful execution here after testing)

## Notes

- The workflow uses n8n's expression syntax `{{ $vars.VARIABLE_NAME }}` for configuration
- Add credentials in n8n before running
- The webhook step is optional — if `WEBHOOK_URL` is empty, the workflow completes silently with the summary in the output
- GitHub API rate limits: 5000 requests/hour with authentication
