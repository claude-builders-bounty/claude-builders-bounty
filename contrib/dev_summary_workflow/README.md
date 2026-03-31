# Weekly Dev Summary Workflow

This n8n workflow automates the generation of weekly development summaries by pulling data from GitHub and using Claude AI to generate a formatted report.

## Overview

The workflow performs the following steps:

1. Triggers weekly via schedule
2. Fetches commits from specified repositories
3. Fetches pull requests from specified repositories
4. Combines the data and sends it to Claude API
5. Generates a Markdown-formatted summary
6. Saves the summary as a Markdown file

## Setup Instructions

### Prerequisites

- An n8n instance running
- GitHub account with appropriate permissions
- Anthropic Claude API key

### Configuration Steps

1. Import the workflow JSON into your n8n instance
2. Set up GitHub credentials in n8n:
   - Go to Credentials → Add Credential
   - Select GitHub
   - Enter your GitHub token with appropriate scopes
3. Set up Claude API credential:
   - Go to Credentials → Add Credential
   - Create a Generic credential type
   - Name it `claudeApiKey`
   - Enter your Anthropic API key
4. Configure the workflow parameters:
   - Update repository owner and name in the GitHub nodes
   - Adjust the schedule timing if needed
   - Modify the Claude model if desired

### Environment Variables

The workflow uses these environment variables:

- `GITHUB_TOKEN`: GitHub personal access token
- `CLAUDE_API_KEY`: Anthropic Claude API key

## Usage

Once configured, the workflow will automatically run weekly and generate a development summary in Markdown format. The summary includes both commit history and pull request activity for the past week.

## Customization

You can customize the workflow by:

- Changing the schedule frequency
- Adding multiple repositories
- Modifying the Claude prompt for different summary styles
- Adjusting the output format

## Troubleshooting

If the workflow fails:

1. Check that all credentials are properly configured
2. Verify GitHub token has necessary permissions
3. Ensure Claude API key is valid and has sufficient quota
4. Review the execution logs in n8n for specific error messages

## Security Notes

- Store API keys securely using n8n's credential system
- Limit GitHub token permissions to only necessary scopes
- Regularly rotate API keys

## License

This workflow configuration is provided under the same license as the parent repository.