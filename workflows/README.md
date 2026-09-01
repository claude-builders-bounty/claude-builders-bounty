 # n8n Weekly Dev Summary Workflow
 
 Automated weekly narrative summary of GitHub repo activity using Claude API.
 
 ## Setup (5 steps)
 
 1. Import `n8n-weekly-dev-summary.json` into your n8n instance
 2. Configure GitHub API credentials (replace `REPLACE_WITH_GITHUB_CRED_ID`)
 3. Configure Anthropic API credentials (replace `REPLACE_WITH_ANTHROPIC_CRED_ID`)
 4. Set workflow variables: `githubOwner`, `githubRepo`, `webhookUrl`, `language` (EN/FR)
 5. Activate the workflow — runs every Friday at 5pm UTC
 
 ## Delivery
 
 Summary is sent via Discord/Slack webhook. To use email instead, replace the
 "Send to Discord/Slack" node with an n8n Email node and configure SMTP.
 
 ## Model
 
 Uses `claude-sonnet-4-20250514` for narrative generation. Update in the Claude
 Summary node if a newer model is preferred.
