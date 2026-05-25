# Weekly Dev Summary — n8n + Claude

An n8n workflow that automatically generates a weekly narrative summary of GitHub repo activity using Claude API.

## 🚀 Installation (5 steps)

1. **Import the workflow** in n8n:
   - Go to **Workflows → Add Workflow → Import from File**
   - Select `weekly_summary.json`

2. **Set up GitHub credentials**:
   - Create a **Header Auth** credential in n8n
   - Header Name: `Authorization`
   - Header Value: `token YOUR_GITHUB_TOKEN` (requires `repo` scope)

3. **Set up Claude API credentials**:
   - Create another **Header Auth** credential
   - Header Name: `x-api-key`
   - Header Value: `sk-ant-...` (your Anthropic API key)

4. **Configure the workflow variables**:
   - In the HTTP Request nodes, update the URL to your repo
   - In the Webhook node, set your destination URL (Slack/Discord/email)
   - Or set `webhook_url` in n8n variables

5. **Activate the workflow**
   - The schedule runs every Friday at 5 PM by default
   - To change: edit the Schedule Trigger node

## ⚙️ How It Works

```
Schedule (Fri 5pm) → Fetch GitHub Data → Merge → Build Prompt → Claude API → Format → Send
```

| Step | Description |
|------|-------------|
| Schedule Trigger | Weekly cron: Friday 5pm |
| Fetch GitHub Data | 3 parallel HTTP requests: commits, closed issues, merged PRs |
| Merge | Combines all 3 data sources |
| Build Prompt | Python code node constructs a structured prompt for Claude |
| Claude API | Calls `claude-sonnet-4-20250514` with the prompt |
| Format Summary | Formats the Claude response as a clean Markdown report |
| Send to Webhook | Delivers to Slack, Discord, email, or any webhook URL |

## 🔧 Configuration

| Variable | Location | Default |
|----------|----------|---------|
| GitHub repo URL | HTTP Request nodes | `owner/repo` |
| Schedule | Schedule Trigger | Friday 5pm |
| Claude model | Claude API node | `claude-sonnet-4-20250514` |
| Delivery channel | Webhook node | Slack webhook |
| Language (EN/FR) | Build Prompt code | English |

## 📸 Example Output

See [SAMPLE_OUTPUT.md](SAMPLE_OUTPUT.md) for a sample generated summary.
