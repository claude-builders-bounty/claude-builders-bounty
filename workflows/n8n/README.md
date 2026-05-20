# n8n Weekly GitHub Summary Workflow

Automated workflow to generate a professional narrative summary of your GitHub repository's activity using Claude AI.

## Setup Instructions

1. **Import Workflow:** Import the `weekly_summary.json` file into your n8n instance.
2. **Configure Credentials:** Add your **GitHub** and **Anthropic** credentials to the respective nodes.
3. **Environment Variables:** Set the following env vars in your n8n environment:
   - `GITHUB_OWNER`: The owner of the repo.
   - `GITHUB_REPO`: The repository name.
   - `WEBHOOK_URL`: Your Discord/Slack webhook URL.
   - `LANGUAGE`: EN or FR (Default: EN).
4. **Trigger:** The workflow is set to run every Friday at 5:00 PM.
5. **Activate:** Toggle the workflow to 'Active'.

## Features
- Fetches all commits, issues, and PRs for the week.
- Uses **Claude 3.5 Sonnet** for high-quality narrative generation.
- Delivers the summary directly to your notification channel.
