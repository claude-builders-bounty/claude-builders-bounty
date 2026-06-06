# Weekly GitHub Activity Summary (n8n + Claude)

Automated weekly workflow that summarizes your GitHub repo activity using Claude AI and delivers it to Discord.

**What it does:** Every Friday at 5pm, it fetches the last 7 days of commits, closed issues, and merged PRs, sends them to Claude for a narrative summary, and posts a rich embed to your Discord channel.

## Setup (5 steps)

### Step 1: Import the workflow
Open n8n → **Workflows** → **Import from File** → select `workflow.json`.

### Step 2: Set environment variables
In n8n, go to **Settings → Variables** and add:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_OWNER` | Repo owner (org or user) | `claude-builders-bounty` |
| `GITHUB_REPO` | Repository name | `claude-builders-bounty` |
| `GITHUB_TOKEN` | GitHub personal access token (needs `repo` scope) | `ghp_xxx` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-xxx` |
| `DISCORD_WEBHOOK_URL` | Discord channel webhook URL | `https://discord.com/api/webhooks/...` |
| `SUMMARY_LANGUAGE` | `EN` for English, `FR` for French | `EN` |

### Step 3: Create credentials in n8n
Go to **Credentials → Add** → search **Header Auth** → create:
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer YOUR_GITHUB_TOKEN`

Then edit each "Get Commits/Issues/PRs" node and select this credential.

### Step 4: Test the workflow
Click **Test Workflow** (play button). Check that:
- GitHub data is fetched (node outputs show arrays)
- Claude returns a summary
- Discord receives the embed

### Step 5: Activate
Toggle the workflow **Active**. It will run automatically every Friday at 5pm (cron: `0 17 * * 5`).

## Architecture

```
Schedule (Fri 5pm) → Set Config → [Commits, Issues, PRs] (parallel)
                                            ↓
                                         Merge
                                            ↓
                                    Format Activity Data
                                            ↓
                                  Claude API (claude-sonnet-4-20250514)
                                            ↓
                                    Discord Webhook
```

## Customization

- **Change schedule:** Edit the "Weekly Friday 5pm" node → change the cron expression (e.g., `0 9 * * 1-5` for weekdays at 9am).
- **Change language:** Set `SUMMARY_LANGUAGE` to `FR` for French summaries.
- **Email delivery:** Replace the Discord node with n8n's built-in Email node.
- **Slack:** Replace Discord node with n8n's Slack node (same webhook pattern).

## Validation

```bash
node validate-workflow.mjs
```

Checks: workflow shape, 9 nodes present, cron trigger, Claude model, configurable variables, README completeness.

## License

MIT
