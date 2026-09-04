# n8n Weekly Dev Summary Workflow

> Automated weekly narrative summary of GitHub repo activity, powered by n8n + Claude API.

## What It Does

Every Friday at 5pm, this workflow:

1. **Calculates the current week's date range** (Monday–Friday)
2. **Fetches from GitHub API**:
   - All commits for the week
   - All closed issues for the week  
   - All merged PRs for the week
3. **Sends data to Claude API** (`claude-sonnet-4-20250514`) to generate a narrative summary
4. **Delivers** the summary via Discord/Slack webhook (or test response)

## Setup (5 Steps)

### Step 1: Import the Workflow
1. Open your n8n instance → **Workflows** → **Import from File**
2. Upload `weekly-dev-summary.json`

### Step 2: Create GitHub Credential
1. Go to **Credentials** → **Add Credential** → **Header Auth**
2. Name: `GitHub Token Auth`
3. Header Name: `Authorization`
4. Header Value: `token YOUR_GITHUB_PERSONAL_ACCESS_TOKEN`

### Step 3: Create Anthropic Credential
1. Go to **Credentials** → **Add Credential** → **Anthropic API**
2. Enter your Anthropic API key

### Step 4: Configure Environment Variables
In your n8n environment (or set in the "Set Week Range & Config" node):

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO_OWNER` | GitHub repo owner | `octocat` |
| `GITHUB_REPO_NAME` | GitHub repo name | `Hello-World` |
| `GITHUB_TOKEN` | GitHub PAT (with repo scope) | `ghp_xxxx` |
| `SUMMARY_LANGUAGE` | Output language | `EN` or `FR` |
| `WEBHOOK_URL` | Discord/Slack webhook URL | `https://discord.com/api/webhooks/...` |

### Step 5: Activate & Test
1. Toggle the workflow **ON**
2. Click **Test Step** on the "Respond" node to verify output
3. It will run automatically every Friday at 5pm

## Configuration

### Change Schedule
Edit the **Schedule Trigger** node to change the day/time.

### Add Email Delivery
Add a **Send Email** node after "Call Claude API" alongside the webhook node.

### Customize Prompt
Edit the **Build Prompt for Claude** node to change the summary style/tone.

## Screenshot

After running, you'll see output like:

```
📋 Weekly Dev Summary Generated!

Here is the summary of September 1, 2026 to September 5, 2026 for **owner/repo**.

## 🔥 Key Accomplishments
- Implemented OAuth2 login flow (#123)
- Fixed memory leak in background worker (#120)
- Added rate limiting middleware (#119)

## 👥 Collaboration Highlights
- @alice and @bob paired on the auth refactor
- 3 community PRs were reviewed and merged

## 📈 Stats
- 12 commits across 5 contributors
- 4 issues closed
- 7 PRs merged
```

## Requirements

- **n8n** >= 1.0 (self-hosted or cloud)
- **GitHub Personal Access Token** with `repo` scope
- **Anthropic API Key** (with Claude access)
- **Discord/Slack Webhook URL** (optional, for delivery)

## License

MIT
