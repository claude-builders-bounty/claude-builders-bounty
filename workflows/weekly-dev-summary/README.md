# Weekly Dev Summary — n8n + Claude API

Automatically generates a narrative weekly development summary for any GitHub repo, powered by n8n and Claude.

## Setup (5 Steps)

### 1. Import the workflow

1. Open your n8n instance
2. Go to **Workflows** → **Add Workflow** → **Import from File**
3. Select `weekly-dev-summary.json`

### 2. Add your GitHub token

1. Create a [GitHub personal access token](https://github.com/settings/tokens) with `repo` scope
2. In n8n, go to **Credentials** → **Add Credential**
3. Type: **Header Auth** → Name: `GitHub Token`
4. Header Name: `Authorization` → Header Value: `Bearer YOUR_GITHUB_TOKEN`

### 3. Add your Anthropic API key

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. In n8n, go to **Credentials** → **Add Credential**
3. Type: **Header Auth** → Name: `Anthropic API Key`
4. Header Name: `x-api-key` → Header Value: `YOUR_ANTHROPIC_KEY`
5. Add a second header: `anthropic-version` → `2023-06-01`

### 4. Set your repo and destination

When running the workflow, set these workflow parameters:

| Parameter | Example | Description |
|---|---|---|
| `repoOwner` | `vercel` | GitHub org or user |
| `repoName` | `next.js` | Repository name |
| `language` | `EN` or `FR` | Summary language |
| `deliveryType` | `discord` or `slack` | Destination type |
| `webhookUrl` | `https://discord.com/api/webhooks/...` | Webhook URL for delivery |

### 5. Activate the schedule

1. Open the imported workflow
2. Toggle **Active** on
3. The workflow runs every **Friday at 5:00 PM UTC**

You can also test it immediately by clicking **Execute Workflow**.

## How It Works

```
Schedule (Fri 5pm)
    │
    ▼
Configure Repo & Language ──┬──► Fetch Commits (GitHub API)
                            ├──► Fetch Merged PRs (GitHub API)
                            │
                            ▼
                        Combine & Build Prompt
                            │
                            ▼
                        Claude API (claude-sonnet-4-20250514)
                            │
                            ▼
                        Extract Summary
                            │
                      ┌─────┴─────┐
                      ▼           ▼
                  Discord     Slack
                  Webhook     Webhook
```

## Customization

- **Language**: Set `language` to `FR` for French summaries (or extend the Code node for other languages)
- **Schedule**: Edit the **Weekly Schedule** node's cron expression (`0 17 * * 5` = Fri 5pm)
- **Destination**: Both Discord and Slack webhook nodes are included; the `webhookUrl` parameter feeds the active one

## Sample Output

See [`examples/sample-output.md`](./examples/sample-output.md) for an example of what the weekly summary looks like.
