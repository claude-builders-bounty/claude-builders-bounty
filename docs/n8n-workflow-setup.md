# n8n Weekly Dev Summary Setup

## Overview
This workflow automatically generates a weekly narrative summary of GitHub repository activity using the Claude API and delivers it via Slack or Discord webhook.

## Setup Instructions

### Step 1: Install n8n
- Download and install n8n from [n8n.io](https://n8n.io/)
- Create an account and log in

### Step 2: Import the Workflow
1. In n8n dashboard, click "Import from file"
2. Select `workflows/weekly-dev-summary.json`
3. Click "Import"

### Step 3: Configure Credentials
1. Go to Credentials > Add Credential
2. Add GitHub Personal Access Token with repo permissions
3. Add Slack/Discord webhook URL for notifications

### Step 4: Configure Workflow Settings
1. Edit the "Prepare Data" node:
   - Set `githubRepo` to your target repository (e.g., `owner/repo`)
   - Set `webhookUrl` to your Slack/Discord webhook
   - Set `language` to "EN" or "FR"
2. Set the schedule trigger to run weekly (e.g., Friday at 5pm)

### Step 5: Test and Activate
1. Click "Execute Workflow" to test
2. Check the execution status and notifications
3. Once working, enable the schedule trigger

## Testing
To verify the workflow:
1. Manually trigger the workflow
2. Check for successful execution in n8n
3. Verify notification arrives in your Slack/Discord channel

## Configuration Options
- `githubRepo`: Target repository (format: `owner/repo`)
- `webhookUrl`: Slack/Discord webhook URL
- `language`: Summary language ("EN" or "FR")
- Schedule: Configure in the Schedule Trigger node

## Notes
- Requires GitHub API access with repo permissions
- Requires Claude API access (automatically configured in n8n)
- First run may take longer as it fetches initial data