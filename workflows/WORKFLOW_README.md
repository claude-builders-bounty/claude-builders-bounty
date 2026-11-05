# Weekly Dev Summary Workflow

Automate your weekly status reports using n8n, GitHub, and Claude.

## Setup Instructions
1. **Import**: Open n8n, click 'Import from File', and select `n8n-weekly-summary-workflow.json`.
2. **GitHub Credentials**: Add your GitHub Personal Access Token in the HTTP Request node.
3. **Claude Credentials**: Add your Anthropic API Key in the Anthropic node.
4. **Configure**: Update the `owner`, `repo`, and `language` variables in the first node.
5. **Webhook**: Set your Discord/Slack webhook URL in the final HTTP Request node.

## Requirements
- n8n instance (Cloud or Self-hosted)
- GitHub PAT with `repo` scope
- Anthropic API Key