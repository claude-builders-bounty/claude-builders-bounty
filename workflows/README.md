# Weekly Dev Summary — n8n Workflow

An **n8n workflow** that automatically generates a narrative summary of your GitHub repository's weekly activity using **Claude API** and delivers it to a **Discord webhook**.

![Workflow Diagram](./screenshot.png)

> **Bounty #5** — Built for [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty)

---

## ✨ What It Does

| Step | Action |
|------|--------|
| 1 | Runs every **Friday at 5pm** (cron trigger) |
| 2 | Fetches **commits**, **closed issues**, and **merged PRs** from the past week via GitHub API |
| 3 | Sends the data to **Claude API** (`claude-sonnet-4-20250514`) to generate an engaging narrative summary |
| 4 | Posts the summary to a **Discord webhook** (or Slack — see customization below) |

---

## ⚙️ Configurable Variables

All variables are set in the **⚙️ Configuration** node (the second node in the workflow). Edit them to match your setup:

| Variable | Description | Default |
|----------|-------------|---------|
| `repoOwner` | GitHub org or user | `your-org` |
| `repoName` | Repository name | `your-repo` |
| `language` | Output language (`EN` or `FR`) | `EN` |
| `claudeModel` | Anthropic model ID | `claude-sonnet-4-20250514` |

The following are loaded from **n8n environment variables** for security:

| Environment Variable | Purpose |
|----------------------|---------|
| `GITHUB_TOKEN` | GitHub personal access token (with `repo` scope) |
| `CLAUDE_API_KEY` | Anthropic API key |
| `DISCORD_WEBHOOK_URL` | Discord channel webhook URL |

---

## 🚀 Setup Instructions (5 Steps)

### 1. Import the workflow

1. Open your **n8n instance**
2. Go to **Workflows** → **Add Workflow** → **Import from File**
3. Select `weekly-dev-summary.json`

### 2. Configure credentials

In n8n, create these **Credentials**:

| Credential Name | Type | Value |
|----------------|------|-------|
| `GitHub Token` | **Header Auth** | Header Name: `Authorization`, Header Value: `Bearer YOUR_GITHUB_TOKEN` |
| `Claude API Key` | **Header Auth** | Header Name: `x-api-key`, Header Value: `YOUR_ANTHROPIC_KEY` |

> **Alternatively**, set environment variables in your `docker-compose.yml` or `.env`:
> ```
> GITHUB_TOKEN=ghp_...
> CLAUDE_API_KEY=sk-ant-...
> DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
> ```

### 3. Set your repo variables

1. Open the **⚙️ Configuration** node
2. Change `repoOwner` to your GitHub org/username
3. Change `repoName` to your repository name
4. Set `language` to `EN` or `FR`

### 4. Create a Discord webhook

1. In your Discord server, go to **Server Settings** → **Integrations** → **Webhooks**
2. Click **New Webhook**, name it `Weekly Dev Summary`, and select a channel
3. Copy the **Webhook URL**
4. Set it as `DISCORD_WEBHOOK_URL` in your n8n environment (or in the **📬 Discord Webhook** node directly)

> **For Slack**: Replace the last node's URL with your Slack webhook URL and adjust the body format to `{"text": "{{ $json.summary }}"}`.

### 5. Activate the workflow

1. Click **Save** then toggle **Active** to ON
2. The workflow will run every **Friday at 5pm** automatically
3. To test immediately, click **Execute Workflow**

---

## 🧪 Test Output Example

```
📊 Weekly Dev Summary — 2026-06-22 to 2026-06-28

Repository: my-org/my-repo
Commits: 23  |  Issues Closed: 5  |  PRs Merged: 7

This was a productive week for my-org/my-repo. The team shipped 7
pull requests spanning the new authentication module, API rate limiting
improvements, and several dependency updates. Notably, PR #142 by @alice
introduced OAuth2 support, closing 3 related issues...
```

---

## 📁 File Structure

```
workflows/
├── weekly-dev-summary.json   # n8n workflow (importable)
└── README.md                 # This file
```

---

## 🔧 Customization Ideas

- **Delivery**: Swap the Discord webhook for **email** (n8n has an SMTP node), **Slack**, or **Telegram**
- **Schedule**: Change the cron expression in the trigger node to any frequency
- **Scope**: Add more GitHub endpoints (releases, stars, forks)
- **Format**: Tweak the prompt in the **🔀 Combine & Prepare Prompt** node to change the tone or structure

---

## 📝 License

MIT
