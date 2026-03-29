# Weekly Dev Summary — n8n Workflow

Automatically generates a narrative summary of a GitHub repository's weekly activity using Claude (`claude-sonnet-4-20250514`) and delivers it to Discord (or email). Runs every Friday at 17:00.

## What It Does

1. **Fetches** the last 7 days of GitHub activity: commits, closed issues, and merged pull requests
2. **Builds** a structured prompt and sends it to Claude API for a professional narrative summary
3. **Delivers** the summary to a Discord channel via webhook

---

## Setup (5 Steps)

### Step 1 — Import the Workflow

In n8n: go to **Workflows → Import from File** and select `weekly-dev-summary.workflow.json`.

> Requires n8n **v1.0 or later**.

---

### Step 2 — Create Credentials

In n8n go to **Settings → Credentials → Add Credential** and create:

| Credential Name | Type | Configuration |
|---|---|---|
| `GitHub Token` | `GitHub API` | Personal Access Token with `repo` (read) scope. Create at [github.com/settings/tokens](https://github.com/settings/tokens). |
| `Anthropic API Key` | `Header Auth` | Name: `x-api-key`, Value: your Anthropic API key from [console.anthropic.com](https://console.anthropic.com). |

> **Security note:** Always use n8n's credential store — never paste raw secrets into node fields.

---

### Step 3 — Configure Variables

Open the **"Set Config Variables"** node and update the four fields:

| Variable | Description | Example |
|---|---|---|
| `GITHUB_OWNER` | GitHub org or username | `octocat` |
| `GITHUB_REPO` | Repository name | `Hello-World` |
| `LANGUAGE` | Summary language | `English` or `French` |
| `DELIVERY_WEBHOOK` | Discord webhook URL | `https://discord.com/api/webhooks/...` |

> **Discord webhook:** In your server go to **Server Settings → Integrations → Webhooks → New Webhook**, copy the URL.

---

### Step 4 — Attach Credentials to Nodes

Select credentials in these nodes:

| Node | Credential to Select |
|---|---|
| `Fetch Commits` | `GitHub Token` |
| `Fetch Closed Issues` | `GitHub Token` |
| `Fetch Merged PRs` | `GitHub Token` |
| `Call Claude API` | `Anthropic API Key` |

---

### Step 5 — Activate & Test

- Toggle the workflow to **Active** → it will run automatically every Friday at 17:00.
- To test immediately, click **"Execute Workflow"** on the canvas and verify all nodes turn green and your Discord channel receives the message.

---

## Workflow Architecture

