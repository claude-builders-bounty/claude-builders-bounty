# n8n + Claude API Weekly Dev Summary Setup Guide

This guide provides step-by-step instructions to set up an automated weekly development summary using n8n and the Claude API.

## Prerequisites

- n8n installed (desktop or cloud version)
- GitHub account with access to the target repository
- Anthropic API key with access to Claude

## Step 1: Create a GitHub Personal Access Token

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Generate a new token with these scopes:
   - `repo` (full control of public/private repositories)
   - `issues` (read and write)
   - `pull_requests` (read and write)
3. Copy and save the token securely

## Step 2: Get Claude API Key

1. Go to [Anthropic Console](https://console.anthropic.com)
2. Create a new API key or use an existing one
3. Note the API key for later use

## Step 3: Set Up n8n Environment Variables

In n8n:
1. Go to Settings → Environment Variables
2. Add these variables:
   - `GITHUB_TOKEN`: Your GitHub personal access token
   - `CLAUDE_API_KEY`: Your Claude API key

## Step 4: Create the n8n Workflow

### 4.1 Schedule Trigger

1. Add a "Schedule" trigger node
2. Configure to run weekly (e.g., every Monday at 9:00 AM)

### 4.2 GitHub Issues Node

1. Add a "GitHub" node
2. Configure to fetch issues:
   - Operation: "Search Issues"
   - Repository: [owner]/[repo]
   - State: "open"
   - Query: "is:issue"

### 4.3 Filter for Unrewarded Issues

1. Add a "Filter" node
2. Configure to filter issues that:
   - Don't contain "/opire create" in the body
   - Don't have the label "rewarded"

### 4.4 GitHub PRs Node

1. Add another "GitHub" node
2. Configure to pull requests:
   - Operation: "Get Pull Requests"
   - Repository: [owner]/[repo]
   - State: "all"

### 4.5 Claude API Node

1. Add an "HTTP Request" node
2. Configure to call Claude API:
   - Method: POST
   - URL: https://api.anthropic.com/v1/messages
   - Headers:
     - `x-api-key`:={{ $CLAUDE_API_KEY }}
     - `anthropic-version`: 2023-06-01
     - `content-type`: application/json
   - Body (JSON):
     ```json
     {
       "model": "claude-3-sonnet-20240229",
       "max_tokens": 1000,
       "messages": [
         {
           "role": "user",
           "content": "Create a weekly development summary based on these GitHub issues and pull requests. Include: 1) Issues opened this week, 2) Pull requests merged this week, 3) Key discussions, 4) Upcoming work. Format as structured markdown.\n\nIssues:\n{{ $json.allIssues }}\n\nPull Requests:\n{{ $json.allPRs }}"
         }
       ]
     }
     ```

### 4.6 Format Output

1. Add a "Code" node to format the Claude response
2. Extract the content from the API response

### 4.7 Send Summary (Optional)

1. Add a "Webhook" or "Email" node to send the summary
2. Configure with your preferred notification method

## Step 5: Test the Workflow

1. Run the workflow manually to test
2. Verify it fetches issues and PRs correctly
3. Check that Claude generates a proper summary
4. Test error handling for API failures

## Step 6: Schedule and Monitor

1. Set the schedule as needed
2. Monitor execution in n8n's execution history
3. Set up alerts for failures

## Error Handling

Add error handling nodes:
- GitHub API rate limiting: Add exponential backoff
- Claude API errors: Retry with different parameters
- Missing data: Send alert to maintainers

## Troubleshooting

- **GitHub authentication issues**: Verify token scopes
- **Claude API errors**: Check API key and model availability
- **Empty results**: Verify repository access and permissions

## Security Notes

- Never commit API keys to version control
- Use environment variables in n8n
- Regularly rotate API keys
- Limit token scopes to minimum necessary

## Next Steps

1. Implement the workflow in your n8n environment
2. Test thoroughly with your specific repository
3. Customize the prompt based on your needs
4. Set up monitoring and alerts

This setup provides a complete solution for automated weekly development summaries using n8n and Claude API.