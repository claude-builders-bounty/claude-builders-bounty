# Weekly Dev Summary Workflow

## Setup Instructions

1. **Import the workflow**  
   In your n8n instance, go to Workflows > Import and select the `weekly-dev-summary.json` file.

2. **Configure GitHub credentials**  
   - Go to Credentials > GitHub and enter your personal access token with repo scope
   - Set the target repository owner and name

3. **Configure Claude API**  
   - Go to Credentials > Anthropic and enter your Claude API key
   - Select the model `claude-sonnet-4-20250514`

4. **Configure Output**  
   - Set up either:  
     a) Email credentials and recipient  
     b) Webhook URL for Discord/Slack

5. **Test & Enable**  
   - Test the workflow manually to ensure it functions  
   - Enable the weekly cron trigger (e.g., `0 17 * * 5` for Friday 5pm)

Configuration values can be edited directly in the workflow settings.