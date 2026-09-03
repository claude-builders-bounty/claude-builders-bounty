# Claude + n8n Weekly Summary Workflow

## Setup Instructions (5 steps)
1. Import `workflow.json` into your n8n instance.
2. In the "Fetch GitHub Activity" node, configure your GitHub API token in the Headers (if accessing a private repo).
3. Set your Anthropic API Key in the "Claude Sonnet" node.
4. Replace `discordWebhook` with your actual Discord channel webhook URL.
5. Activate the workflow! It will run automatically every Friday at 5 PM.

## Features
- Fetches recent GitHub events.
- Uses `claude-sonnet-4-20250514` for narrative generation.
- Supports EN/FR language switching via input variable.
- Posts directly to Discord.
