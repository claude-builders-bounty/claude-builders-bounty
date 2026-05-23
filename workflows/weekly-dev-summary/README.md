# Weekly Dev Summary n8n Workflow with Claude 🤖

This directory contains a complete, exportable n8n workflow that automatically compiles a weekly narrative summary of a GitHub repository's updates (commits, closed issues, merged PRs) using the Claude API and delivers it to a Discord or Slack channel.

## Features
- **Zero proprietary node dependencies**: Uses standard, cross-version compatible HTTP Request nodes to communicate with GitHub and Anthropic.
- **Auto-Aggregator Code**: A lightweight Javascript node that filters out noise and extracts only updates from the last 7 days.
- **Narrative summaries**: Calls Claude (`claude-3-5-sonnet` or similar) to generate a summary.
- **Localization**: Supports English (EN) and French (FR) summaries.

---

## Setup Instructions (5 Steps)

### Step 1: Import the Workflow
In your n8n workspace, click **Add Workflow** -> **Import from File**, and select [weekly-dev-summary.json](./weekly-dev-summary.json).

### Step 2: Configure variables
Open the **Set Configurations** node and enter:
- `github_owner`: The owner of the GitHub repo.
- `github_repo`: The repository name.
- `discord_webhook_url`: Your Discord integration webhook URL.
- `anthropic_api_key`: Your Anthropic API credential key.
- `language`: `EN` or `FR` for summary output.

### Step 3: Configure execution triggers
By default, the workflow is scheduled via a **Schedule Trigger** node to run every Friday at 5:00 PM. Adjust this schedule as desired.

### Step 4: Run a test execution
Click **Listen for Test Event** or **Execute Workflow** in n8n to test fetching, aggregating, summarizing, and posting a live dev summary to your Discord channel.

### Step 5: Toggle Active
Flip the workflow status toggle in the top-right corner to **Active** to schedule weekly summaries!
