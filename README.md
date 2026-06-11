# Weekly GitHub Repo Summary with Claude

This n8n workflow automatically generates a weekly narrative summary of any GitHub repository's activity using the Claude API.

## Setup (5 steps)

1. **Import workflow**: Download `weekly-repo-summary.json` and import into n8n.
2. **Set credentials**: 
   - GitHub Personal Access Token (use Basic Auth: username + token)
   - Claude API Key (header `x-api-key`)
3. **Configure variables**: Set `REPO`, `DESTINATION_EMAIL`, `CLAUDE_API_KEY`, and optional `LANGUAGE` (EN/FR) in workflow settings.
4. **Activate workflow**: Enable the workflow; it runs every Friday at 5 PM.
5. **Test**: Click "Execute Workflow" and check your email for the summary.

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub API token with repo permissions
- Anthropic API key with access to Claude Sonnet 4

## Files

- `weekly-repo-summary.json`: n8n workflow export
