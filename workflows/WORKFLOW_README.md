# Weekly Dev Summary Workflow

## Setup Instructions
1. **Import**: Open n8n, click 'Import from File', and select `weekly-dev-summary-workflow.json`.
2. **GitHub Auth**: Create a GitHub Personal Access Token and add it to the HTTP Request node.
3. **Claude API**: Add your Anthropic API Key to the Anthropic node credentials.
4. **Configure**: Update the 'Set' node with your `owner`, `repo`, `language`, and `webhook_url`.
5. **Activate**: Toggle the workflow to 'Active' in the top right corner.