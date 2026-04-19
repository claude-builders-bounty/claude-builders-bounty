# 🤖 n8n + Claude: Automated Weekly GitHub Dev Summary

An automated n8n workflow that fetches a GitHub repository's weekly activity (commits, closed issues, merged PRs), uses **Claude Sonnet** to generate a narrative summary, and delivers it to a **Discord** channel every Friday at 5:00 PM.

---

## ⚙️ Setup in 5 Steps

### Step 1 — Import the Workflow
1. Open your n8n instance.
2. Go to **Workflows** → **Import from File**.
3. Select `n8n_github_summary.json`.

### Step 2 — Set GitHub Credentials
1. In the workflow, click any `HTTP Request` node that calls `api.github.com`.
2. Under **Authentication**, add a new **Header Auth** credential:
   - **Name:** `Authorization`
   - **Value:** `Bearer YOUR_GITHUB_TOKEN`
3. Click **Save**.

### Step 3 — Set Anthropic (Claude) Credentials
1. Click the **Anthropic** HTTP Request node.
2. Under **Authentication**, add a new **Header Auth** credential:
   - **Name:** `x-api-key`
   - **Value:** `YOUR_ANTHROPIC_API_KEY`
3. Click **Save**.

### Step 4 — Configure Your Variables
Click the **📋 Config** Set node at the top of the workflow and fill in:

| Variable         | Description                             | Example                        |
|------------------|-----------------------------------------|--------------------------------|
| `GITHUB_OWNER`   | Repo owner (user or org)                | `vercel`                       |
| `GITHUB_REPO`    | Repository name                         | `next.js`                      |
| `DISCORD_WEBHOOK`| Your Discord webhook URL                | `https://discord.com/api/...`  |
| `LANGUAGE`       | Summary language (`EN` or `FR`)         | `EN`                           |

### Step 5 — Activate the Workflow
Toggle the workflow to **Active** in the top-right corner. It will fire automatically every **Friday at 5:00 PM** (UTC).

---

## 🔧 Manual Test
To test immediately without waiting for Friday, click the **Schedule Trigger** node (named **"Every Friday 5PM"**) and hit **"Test step"** — this will run the entire pipeline on demand.

---

## 📦 Requirements
- n8n `>= 1.0.0` (self-hosted or cloud)
- GitHub Personal Access Token (read access)
- Anthropic API Key
- Discord Webhook URL
