# Weekly Dev Summary (n8n Workflow)

Automatically generates a weekly narrative summary of a GitHub repo's activity.

## Features

- Triggered weekly via Schedule
- Fetches recent commits, PRs, and issues
- Generates a narrative summary using OpenAI GPT-4
- Sends the summary to Slack

## Installation

1. Import `workflow.json` into n8n
2. Configure credentials:
   - GitHub API token
   - OpenAI API key
   - Slack webhook
3. Set the repository owner/name in the GitHub nodes
4. Activate the workflow

## Output

A concise weekly narrative highlighting:
- Key commits and features
- Merged/opened PRs
- Notable issues
- Overall project progress
