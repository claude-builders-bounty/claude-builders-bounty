# Weekly Dev Summary — n8n + Claude

Generate a narrative weekly development summary from GitHub activity using n8n and Claude.

## Quick Start (5 Steps)

### 1. Install n8n
```bash
docker run -d --name n8n -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n
```
Open http://localhost:5678

### 2. Import the Workflow
- Go to **Workflows** → **Add Workflow** → **Import from File**
- Select `Weekly_Dev_Summary_Workflow.json`

### 3. Configure Credentials
Set up two credentials in n8n:

**GitHub Token** (Personal Access Token)
- Type: Header Auth
- Header Name: `Authorization`
- Header Value: `Bearer ghp_...` (your token with `repo` scope)

**Claude API Key**
- Type: Header Auth
- Header Name: `x-api-key`
- Header Value: `sk-ant-...` (from [console.anthropic.com](https://console.anthropic.com))

### 4. Configure Variables
Edit the **Set Date Range** node and update:
- `repo` → your GitHub repo (e.g., `my-org/my-project`)
- `deliveryChannel` → `slack` (or `email`)
- `language` → `EN` (or `FR`)

### 5. Wire Delivery
The workflow delivers to **Slack** by default. Swap the **Send Summary** node:
- **Slack**: Use the built-in Slack node (configure OAuth)
- **Discord**: Replace with Discord Webhook node
- **Email**: Replace with Email node (SMTP)

## Test It

Click **Execute Workflow** in the n8n editor. You should see:
1. GitHub API fetches commits, issues, and PRs
2. Claude generates a narrative summary
3. Summary arrives in your configured channel

## Screenshot

![n8n workflow showing the pipeline from cron trigger through GitHub API to Claude and Slack](screenshot.png)

> *(Add your screenshot here after testing)*

## Customization

| Variable | Location | Description |
|---|---|---|
| `repo` | Set Date Range node | Target GitHub repo |
| `deliveryChannel` | Set Date Range node | `slack`, `discord`, or `email` |
| `language` | Set Date Range node | Output language |
| Cron schedule | Schedule Trigger node | Currently Friday 5pm |

## How It Works

```
Cron (Fri 5pm)
  → Set date range & config
  → Fetch commits (GitHub API)
  → Fetch closed issues (GitHub API)    (parallel)
  → Fetch merged PRs (GitHub API)
  → Merge all data
  → Build structured prompt
  → Call Claude API (claude-sonnet-4-20250514)
  → Extract summary text
  → Deliver to Slack/Discord/Email
```
