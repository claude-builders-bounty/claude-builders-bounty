# Bounty #5 — Automated Weekly Dev Summary (n8n Workflow)

**Bounty:** $200 — `claude-builders-bounty/claude-builders-bounty` Issue #5  
**Author:** Hermes Agent

This n8n workflow automatically generates a **weekly development summary** using GitHub API data and Claude AI. It runs every **Friday at 5 PM**, fetches the week's commits, closed issues, and merged PRs, calls **Claude Sonnet 4 (claude-sonnet-4-20250514)** to produce a narrative summary, and delivers it to your team's webhook (Slack, Discord, or any HTTP endpoint).

---

## Setup (5 Steps)

### 1. Import the Workflow

1. Open your **n8n instance** (self-hosted or n8n.cloud).
2. Go to **Workflows** → **Add Workflow**.
3. Click the **Import** button (or press `Ctrl+I` / `Cmd+I`).
4. Select the file `weekly-dev-summary.json` from this directory.
5. The workflow will appear with all nodes and connections pre-configured.

### 2. Set Up GitHub API Credentials

1. **Generate a GitHub Personal Access Token (PAT):**
   - Go to GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**.
   - Create a token with `repo` scope (for private repos) or `public_repo` (for public repos).
   - Copy the token value.

2. **Add the credential in n8n:**
   - In n8n, go to **Credentials** → **Add Credential**.
   - Choose **Header Auth** (type: `httpHeaderAuth`).
   - Set **Name** to `GitHub API Token`.
   - Set **Header Name** to `Authorization`.
   - Set **Header Value** to `token YOUR_GITHUB_TOKEN` (e.g. `token ghp_abc123...`).
   - Save.

3. **Ensure** the `Get Commits`, `Get Issues`, and `Get PRs` nodes are linked to this credential.

### 3. Set Up Claude API Credentials

1. **Get a Claude API Key:**
   - Go to [console.anthropic.com](https://console.anthropic.com) → **API Keys**.
   - Create a new key and copy it.

2. **Add the credential in n8n:**
   - Go to **Credentials** → **Add Credential**.
   - Choose **Header Auth** (type: `httpHeaderAuth`).
   - Set **Name** to `Claude API Key`.
   - Set **Header Name** to `x-api-key`.
   - Set **Header Value** to your Claude API key.
   - Save.

3. **Ensure** the `Generate Summary with Claude` node is linked to this credential.

### 4. Configure Variables

Open the workflow and set the **Workflow-Level Variables** (found under **Workflow Settings** → **Variables**):

| Variable | Description | Example |
|---|---|---|
| `repoUrl` | GitHub API URL for your repo | `https://api.github.com/repos/your-org/your-repo` |
| `webhookUrl` | Destination URL for the summary | `https://hooks.slack.com/services/...` or Discord webhook |
| `language` | Output language code | `EN` (English), `FR` (French), or `CN` (Chinese) |
| `sinceDate` | (Optional) Override the "since" date for testing. Leave empty for automatic 7-day window. | `2026-05-14` |

**Tip for Slack:** Use a Slack Incoming Webhook URL. The workflow sends a JSON payload with a `text` field, which Slack renders directly.

**Tip for Discord:** Use a Discord Webhook URL. Discord also accepts the `text` field in the JSON body.

### 5. Activate the Workflow

1. Click **Save** to persist your changes.
2. Toggle the **Active** switch in the top-right corner to `ON`.
3. The workflow will now run automatically every **Friday at 5:00 PM**.
4. To test immediately, click **Execute Workflow** to run it manually.

---

## Workflow Structure

```
Weekly Schedule (cron: 0 17 * * 5)
    │
    ├──► Get Commits (GitHub API)
    ├──► Get Issues (GitHub API)
    └──► Get PRs (GitHub API)
         │
         └──► Combine Data (Code node)
              │
              └──► Generate Summary with Claude (Anthropic API)
                   │
                   └──► Extract Summary Text (Code node)
                        │
                        └──► Send to Webhook (Slack/Discord)
```

Each node is fully configurable — you can adjust the cron schedule, API parameters, Claude model, and webhook payload format.

---

## Testing Notes

⚠️ **This workflow was manually constructed based on n8n's documented JSON schema and has not been tested against a live n8n instance.** While the structure follows n8n's export format and should import cleanly, there may be minor differences depending on your n8n version.

**Before activating, test the workflow:**
1. Import the workflow as described above.
2. **Execute Workflow** manually to check that:
   - GitHub API requests return data (check for 200 status codes).
   - The Combine Data node outputs a well-formed JSON object.
   - Claude API call succeeds (check for 200 response).
   - The webhook delivers the message correctly.
3. If any node errors, check:
   - Credentials are correctly linked (IDs may need to be re-assigned after import).
   - Expressions in URL fields and body parameters have correct syntax.
   - Your webhook URL is reachable from your n8n instance.

---

## Customization

- **Change schedule:** Edit the `Weekly Schedule` node's cron expression (default: `0 17 * * 5` = Friday 5 PM).
- **Change Claude model:** Edit the `model` field in the `Generate Summary with Claude` node.
- **Change output format:** Edit the `Send to Webhook` node's body parameters to match your webhook's expected format.
- **Add more data sources:** Add additional HTTP Request nodes and connect them to the `Combine Data` code node.

---

## Files

| File | Description |
|---|---|
| `weekly-dev-summary.json` | The n8n workflow (importable) |
| `sample-output.md` | Example of a generated weekly summary |
| `README.md` | This file |
