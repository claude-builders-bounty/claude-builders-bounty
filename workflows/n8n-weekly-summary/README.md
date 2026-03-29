# n8n Weekly Dev Summary Workflow

An automated n8n workflow that fetches your GitHub repository's weekly activity (Commits + Merged PRs), uses Anthropic's Claude API to generate an engaging narrative summary, and posts the result directly to a Discord Webhook.

## Setup Instructions

1. **Import the Workflow**
   Open your n8n instance. Go to `Workflows` -> `Add Workflow` -> `Import from File` and select the `workflow.json` file in this directory.

2. **Configure GitHub Credentials**
   In the `Get Recent Commits` and `Get Merged PRs` nodes, click `Credential for Http Header Auth` -> `Create New`.
   - Name: `Authorization`
   - Value: `token YOUR_GITHUB_PERSONAL_ACCESS_TOKEN`

3. **Configure Anthropic Credentials**
   In the `Claude API` node, click `Credential for Http Header Auth` -> `Create New`.
   - Name: `x-api-key`
   - Value: `YOUR_ANTHROPIC_API_KEY`

4. **Set Your Variables**
   Open the `Configuration Variables` node and update the values:
   - `githubRepo`: e.g., `owner/repo`
   - `language`: `EN` or `FR`
   - `discordWebhookUrl`: Your Discord channel webhook URL

5. **Activate**
   Toggle the workflow to `Active` in the top right corner. It will automatically run every Friday at 5:00 PM. (You can also click `Test Workflow` to run it immediately).
