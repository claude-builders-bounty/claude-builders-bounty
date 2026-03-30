const fs = require('fs');

const workflow = {
  name: "Weekly Claude Dev Summary",
  nodes: [
    {
      parameters: { rule: { type: "cron", value: "0 17 * * 5" } },
      name: "Schedule Trigger",
      type: "n8n-nodes-base.scheduleTrigger",
      typeVersion: 1.1,
      position: [0, 200],
      id: "trigger_1"
    },
    {
      parameters: {
        keepOnlySet: true,
        values: {
          string: [
            { name: "github_repo", value: "facebook/react" },
            { name: "discord_webhook_url", value: "https://discord.com/api/webhooks/..." },
            { name: "language", value: "EN" },
            { name: "github_token", value: "YOUR_GITHUB_TOKEN" },
            { name: "anthropic_api_key", value: "YOUR_ANTHROPIC_KEY" }
          ]
        }
      },
      name: "Configuration",
      type: "n8n-nodes-base.set",
      typeVersion: 2,
      position: [200, 200],
      id: "config_1"
    },
    {
      parameters: {
        jsCode: `
// Compute timestamps for the last 7 days
const lastWeek = new Date();
lastWeek.setDate(lastWeek.getDate() - 7);
return [{ json: { since: lastWeek.toISOString() } }];
        `
      },
      name: "Calculate Dates",
      type: "n8n-nodes-base.code",
      typeVersion: 1,
      position: [400, 200],
      id: "date_1"
    },
    {
      parameters: {
        method: "GET",
        url: "={{ 'https://api.github.com/repos/' + $('Configuration').item.json.github_repo + '/commits?since=' + $('Calculate Dates').item.json.since }}",
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: "Authorization", value: "={{ 'Bearer ' + $('Configuration').item.json.github_token }}" },
            { name: "User-Agent", value: "n8n-automation" }
          ]
        }
      },
      name: "Fetch Commits",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.1,
      position: [600, 200],
      id: "http_github_1"
    },
    {
      parameters: {
        jsCode: `
const commits = items.map(i => i.json.commit.message).slice(0, 30).join('\\n');
return [{ json: { commitText: commits } }];
        `
      },
      name: "Format Commits",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [800, 200],
      id: "format_1"
    },
    {
      parameters: {
        method: "POST",
        url: "https://api.anthropic.com/v1/messages",
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: "x-api-key", value: "={{ $('Configuration').item.json.anthropic_api_key }}" },
            { name: "anthropic-version", value: "2023-06-01" },
            { name: "Content-Type", value: "application/json" }
          ]
        },
        sendBody: true,
        specifyBody: "json",
        jsonBody: "={ \"model\": \"claude-sonnet-4-20250514\", \"max_tokens\": 1024, \"messages\": [ { \"role\": \"user\", \"content\": \"Write a weekly narrative summary of these github commits in \" + $('Configuration').item.json.language + \":\\n\" + $json.commitText } ] }"
      },
      name: "Claude Analysis",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.1,
      position: [1000, 200],
      id: "http_claude_1"
    },
    {
      parameters: {
        method: "POST",
        url: "={{ $('Configuration').item.json.discord_webhook_url }}",
        sendBody: true,
        specifyBody: "json",
        jsonBody: "={ \"content\": \"**Weekly Repository Summary**\\n\\n\" + $json.content[0].text }"
      },
      name: "Discord Webhook",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.1,
      position: [1200, 200],
      id: "http_discord_1"
    }
  ],
  connections: {
    "Schedule Trigger": { main: [ [ { node: "Configuration", type: "main", index: 0 } ] ] },
    "Configuration": { main: [ [ { node: "Calculate Dates", type: "main", index: 0 } ] ] },
    "Calculate Dates": { main: [ [ { node: "Fetch Commits", type: "main", index: 0 } ] ] },
    "Fetch Commits": { main: [ [ { node: "Format Commits", type: "main", index: 0 } ] ] },
    "Format Commits": { main: [ [ { node: "Claude Analysis", type: "main", index: 0 } ] ] },
    "Claude Analysis": { main: [ [ { node: "Discord Webhook", type: "main", index: 0 } ] ] }
  },
  settings: { executionOrder: "v1" }
};

fs.writeFileSync('workflow.json', JSON.stringify(workflow, null, 2));
console.log('Successfully generated workflow.json!');
