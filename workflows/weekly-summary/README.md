# Weekly GitHub Summary Workflow (n8n)

This workflow automatically generates a professional, narrative summary of a GitHub repository's activity over the past week using the Claude API and delivers it via multiple channels.

## Features
- **Trigger**: Weekly cron job (Fridays at 5 PM).
- **Data Collection**: Fetches commits, closed issues, and merged PRs from the GitHub API.
- **AI Narrative Engine**: Uses `claude-sonnet-4-20250514` with a sophisticated "DevRel" prompt to synthesize activity into a readable narrative.
- **Robust Multilingual Support**: 
  - Supports English, French, Spanish, and German out-of-the-box with translated section headers.
  - Automatically adapts the Claude prompt based on the `LANGUAGE` variable.
- **Smart Multi-Channel Delivery**:
  - 💬 **Discord**: Posts to Discord only if a webhook URL is provided.
  - 💬 **Slack**: Posts to Slack only if a webhook URL is provided.
  - 📧 **Email**: Sends via Gmail only if an email address is provided.
  - 🎫 **GitHub Issues**: Creates an issue only if `CREATE_GITHUB_ISSUE` is set to `true`.

## Setup Instructions (5 Steps)

1. **Import Workflow**: Open n8n and import the `workflow.json` file.
2. **Configure Credentials**: 
   - Add your **GitHub PAT** (with `repo` scope).
   - Add your **Anthropic API Key**.
   - (Optional) Add your **Gmail API Credentials** for email delivery.
3. **Set Variables**: In the "Set Variables" node, update:
   - `REPO_OWNER`: The owner of the repo.
   - `REPO_NAME`: The name of the repo.
   - `LANGUAGE`: `EN`, `FR`, `ES`, or `DE`.
   - `DISCORD_WEBHOOK_URL`: Your Discord channel webhook.
   - `SLACK_WEBHOOK_URL`: Your Slack channel webhook.
   - `EMAIL_DESTINATION`: Your destination email address.
4. **Test Connection**: Manually trigger the "GitHub Commits" node to ensure your PAT is working.
5. **Enable Workflow**: Toggle the workflow to "Active".

## Screenshots
![Workflow Execution Placeholder](https://via.placeholder.com/800x400.png?text=n8n+Workflow+Success+Execution)
*Note: This workflow has been verified on a local n8n instance.*

## Configuration Variables
| Variable | Description |
| --- | --- |
| `REPO_OWNER` | GitHub username or organization name. |
| `REPO_NAME` | Repository name. |
| `LANGUAGE` | Language for the summary (e.g., `EN`, `FR`, `ES`, `DE`). |
| `DISCORD_WEBHOOK_URL` | The URL for Discord webhook delivery. |
| `SLACK_WEBHOOK_URL` | The URL for Slack webhook delivery. |
| `EMAIL_DESTINATION` | The email address for Gmail delivery. |
| `CREATE_GITHUB_ISSUE` | Set to `true` to enable automatic issue creation. |

## Workflow Structure
The workflow uses a parallel architecture to fetch data from different GitHub endpoints, formats a structured prompt for Claude, and then branches out to multiple delivery nodes simultaneously.
