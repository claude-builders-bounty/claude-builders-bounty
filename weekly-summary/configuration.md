# Advanced Configuration

The n8n workflow is designed to be easily customized to fit your specific needs. Here are a few ways to tweak the setup:

## Changing the Target Repository
By default, the workflow is configured to track `claude-builders-bounty/claude-builders-bounty`. 
To track a different repository:
1. Open the **"Set Config"** Code node.
2. Update the `owner` and `repo` constants at the top of the script:
   ```javascript
   const owner = 'your-org-or-username';
   const repo = 'your-repo-name';
   ```

## Language Configuration (EN/FR)
You can instruct Claude to generate the summary in a different language, such as French.
1. Open the **"Aggregate Data & Build Prompt"** Code node.
2. Modify the `prompt` string to specify the desired language explicitly:
   ```javascript
   // Example for French:
   const prompt = `... Please write it in an engaging style, highlighting major changes. Format as Markdown. The final output MUST be in French.`;
   ```

## Custom Output Destinations
The workflow currently ends with a Discord Webhook node. You can easily swap this out to post the summary to a different platform:
- **Slack**: Delete the Discord node and add a Slack node, mapping `{{$json.content[0].text}}` to the message field.
- **Email**: Add an Email node (or SendGrid/Mailgun) to email the summary to a mailing list.
- **Notion**: Add a Notion node to append the summary as a new page in a database.
