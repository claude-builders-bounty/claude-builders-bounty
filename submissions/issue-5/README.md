# n8n + Claude Code — Weekly Dev Summary Workflow

Automated weekly narrative summary of GitHub repo activity, powered by Claude Sonnet 4.

## What It Does

Every Friday at 5pm, this workflow:
1. Fetches the last 7 days of commits, closed issues, and merged PRs from a GitHub repo
2. Formats them into a structured report
3. Sends the report to Claude Sonnet 4 for a narrative summary
4. Posts the summary to a Discord channel

## Workflow Architecture

```
Schedule Trigger → Config → ┬─ GitHub Commits
                              ├─ GitHub Closed Issues    → Wait for All GitHub Data → Merge & Format Data → Claude Sonnet 4 → Extract Summary → Send to Discord
                              └─ GitHub Merged PRs
```

**10 nodes total:**
| Node | Type | Purpose |
|------|------|---------|
| Every Friday 5pm | Schedule Trigger | Weekly cron (Friday 5pm) |
| Config | Set | Central config (repo, keys, language) |
| GitHub Commits | HTTP Request | Fetch recent commits |
| GitHub Closed Issues | HTTP Request | Fetch recently closed issues |
| GitHub Merged PRs | HTTP Request | Fetch recently merged PRs |
| Wait for All GitHub Data | Merge (Append) | Ensures all 3 GitHub branches complete before proceeding |
| Merge & Format Data | Code (JS) | Structured markdown report from raw data |
| Claude Sonnet 4 | HTTP Request | Claude API call for narrative summary |
| Extract Summary | Set | Extract Claude's response text |
| Send to Discord | HTTP Request | Post to Discord webhook |

## Setup Instructions (Step by Step)

### Prerequisites
- n8n v2.30+ (self-hosted or n8n Cloud)
- Anthropic API key with Claude Sonnet 4 access
- GitHub personal access token (repo scope)
- Discord webhook URL

### Step 1: Import the Workflow

1. Open n8n
2. Click **⋮** (three dots) → **Import from File**
3. Select `workflow.json` from this directory
4. The workflow will appear in your workspace

### Step 2: Configure Environment Variables

Set these environment variables in your n8n instance:

```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export GITHUB_TOKEN="ghp_your-token-here"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/your-webhook-here"
```

**For Docker deployments**, add them to your `docker run` or `docker-compose.yml`:
```yaml
environment:
  - ANTHROPIC_API_KEY=sk-ant-your-key-here
  - GITHUB_TOKEN=ghp_your-token-here
  - DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-here
```

### Step 3: Configure the Repo

Open the **Config** node and update:
- `GITHUB_REPO` — your GitHub repo in `owner/repo` format (e.g., `myorg/myproject`)
- `LANGUAGE` — `EN` for English or `FR` for French summaries

### Step 4: Test the Workflow

**Do NOT activate the workflow to test it.** Instead:

1. Open the workflow in the n8n editor
2. Click **"Execute Workflow"** (the play button at the bottom)
3. This runs the entire pipeline manually without waiting for the schedule
4. Check each node's output by clicking on it — green = success, red = error

**Common issues:**
- If GitHub nodes return 401: your `GITHUB_TOKEN` env var is missing or invalid
- If Claude node returns 401: your `ANTHROPIC_API_KEY` is missing or invalid
- If Merge & Format Data shows "Invalid expression": ensure the Config node ran first (check execution order)

### Step 5: Activate for Automatic Weekly Runs

Once tested successfully:
1. Click the **Active** toggle in the top-right corner
2. The schedule trigger will fire every Friday at 5pm (configurable in the trigger node)

## Customization

### Change the Schedule
Edit the **Every Friday 5pm** node:
- `weeksInterval: 1` = every week
- `triggerAtDay: 5` = Friday (0=Monday, 6=Sunday)
- `triggerAtHour: 17` = 5pm (24h format)

### Change the Claude Model
Edit the **Claude Sonnet 4** HTTP Request node:
- `model`: change to `claude-sonnet-4-5-20250929`, `claude-opus-4-6`, etc.
- `max_tokens`: increase for longer summaries (default: 2048)

### Change the Output Channel
Replace the **Send to Discord** node with Slack, Email, or any HTTP endpoint.

## Key Design Decisions

1. **Merge (Append) node** — ensures all 3 GitHub API calls complete before formatting. Without this, the Code node fires prematurely and misses data.
2. **Config node** — single source of truth for repo name, tokens, and language. All nodes reference it via `$('Config').first().json`.
3. **Claude HTTP Request** (not n8n AI Agent node) — more portable, fewer credential steps, works with any Anthropic API key.
4. **Connection types** — all connections use `"type": "main"` as required by n8n's engine.

## Troubleshooting

### "Cannot read properties of undefined (reading 'nodeName')"
This occurs if workflow connections use node type strings (like `"n8n-nodes-base.httpRequest"`) instead of `"main"`. The included `workflow.json` is already correct.

### "Cannot assign to read only property"
This occurs if a Code node tries to access `$('Config').item.json` across a Merge node boundary. Use `$('Config').first().json` instead — it works across the full execution graph.

### Workflow won't activate
Check that all connections have `"type": "main"` and no node has invalid configuration. n8n silently rejects activation if validation fails.

## Cost Estimate

- GitHub API: free (with token, 5000 requests/hour)
- Claude Sonnet 4 API: ~$0.003 per execution (typical summary is ~1500 input + 500 output tokens)
- Total weekly cost: ~$0.003 (less than $0.20/year)
