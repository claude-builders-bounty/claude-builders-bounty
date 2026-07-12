# Weekly Dev Summary — n8n Workflow

Automatically generates a narrative summary of a GitHub repo's weekly activity
using the Claude API, delivered via email or webhook every Friday.

## Setup (5 steps)

### 1. Import the workflow into n8n

- Open your n8n instance (cloud or self-hosted)
- Go to **Workflows** → **Import from File**
- Select `weekly-dev-summary.json` from this folder
- Save the workflow

### 2. Configure credentials

The workflow needs three credentials. Create them in **Settings → Credentials**:

| Credential | Type | Required fields |
|------------|------|-----------------|
| **GitHub API** | HTTP Header Auth | Name: `Authorization`, Value: `Bearer <your_github_token>` |
| **Claude API** | HTTP Header Auth | Name: `x-api-key`, Value: `<your_anthropic_api_key>` |
| **Delivery** | SMTP (email) **or** HTTP Header Auth (webhook) | See step 3 |

> GitHub token needs `repo` scope for private repos, or `public_repo` for public ones.

### 3. Choose delivery method

**Option A — Email (SMTP):**
- Create an SMTP credential with your email provider settings
- Set the workflow variable `DELIVERY_METHOD` to `email`
- Set `EMAIL_TO` to the recipient address

**Option B — Discord/Slack Webhook:**
- Create an HTTP Header Auth credential (no header needed, just the base URL)
- Set the workflow variable `DELIVERY_METHOD` to `webhook`
- Set `WEBHOOK_URL` to your Discord or Slack webhook URL

### 4. Set workflow variables

Open the workflow and configure these variables (click the **Variables** button):

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | `claude-builders-bounty/claude-builders-bounty` | Owner/repo to summarize |
| `LANGUAGE` | `EN` | `EN` for English, `FR` for French |
| `DELIVERY_METHOD` | `email` | `email` or `webhook` |
| `EMAIL_TO` | `team@example.com` | Recipient email (if using email) |
| `WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Webhook URL (if using webhook) |

### 5. Activate the workflow

- Toggle the **Active** switch (top-right)
- The workflow will run every Friday at 5pm UTC
- To test immediately: click **Execute Workflow**

## How it works

