# Automated Weekly Dev Summary Workflow with n8n and Claude API: A Comprehensive Tutorial

## Introduction

In this tutorial, you will learn how to build an automated workflow using **n8n** (a node.js-based automation tool) that integrates with the **Claude** AI API. The goal is to generate a narrative summary of your GitHub repository's activity each week and deliver it via email or a Discord/Slack webhook. This process involves fetching recent commits, closed issues, and merged pull requests from your GitHub repository, generating a summary using Claude's API, and then sending the summary.

## Prerequisites

Before you begin, ensure that you have the following:

- A **GitHub** account with access to the repository you wish to track.
- An **n8n** instance available. You can sign up for one at <https://n8n.io/> or use a self-hosted instance.
- An **Anthropic** (Claude) API key, which allows you to interact with Claude's API.

## Step 1: Setting Up n8n

1. **Create an n8n Instance**: If you don't already have one, create an n8n account at <https://n8n.io/>. Follow the on-screen instructions to set up your instance.
2. **Install the GitHub Node and Claude Nodes**: Go to the "Node Library" section in n8n (found under Settings > Nodes & Webhooks) and install the following nodes:
   - `GitHub`
   - `Claude AI`

## Step 2: Configuring the GitHub Node

1. **Add a New Node**: In your workflow, click on the "+" button to add a new node.
2. **Select "GitHub" Node**: Search for and select the `GitHub` node.
3. **Configure Auth**: Click on the gear icon next to "Authentication" to configure authentication with GitHub. Follow these steps:
   - Enter your GitHub credentials (username and password or token).
   - Select the repository you wish to track.

## Step 3: Fetching Data from GitHub

1. **Add a New Node**: Add another `GitHub` node in your workflow.
2. **Configure Node**: Configure this node to fetch data on commits, closed issues, and merged pull requests:
   - Set "Action" to `List Repositories`.
   - Specify the repository by name or ID (e.g., `my-repo`).
   - Set the "Filter" option to only retrieve recent activity for a specific time period.

## Step 4: Generating Summary with Claude

1. **Add a New Node**: Add another node in your workflow.
2. **Select "Claude AI" Node**: Search and select the `Claude AI` node.
3. **Configure Auth**: Click on the gear icon next to "Authentication" to configure authentication with Claude's API using your API key.
4. **Set Up Prompt**: In the "Prompt" field, construct a prompt that will be sent to Claude for generating the narrative summary. Example:
   ```plaintext
   Generate a weekly summary of recent activity in {repository_name}, including commits, closed issues, and merged pull requests.
   ```
5. **Configure Response Handling**: Configure the node to handle the response from Claude appropriately.

## Step 5: Delivering the Summary

1. **Add an Email Node or Webhook Node**:
   - If you choose email, add a `Send Mail` node and configure it with your email settings.
   - If you prefer Discord/Slack, add a `Discord Webhook` or `Slack Incoming Webhook` node and set up the appropriate channel.

2. **Configure Node**: Set the destination for the summary to be delivered via the chosen method (email address or webhook URL).

## Step 6: Scheduling

1. **Add a Schedule Node**:
   - Add an `Schedule` node in your workflow.
   - Configure it to run weekly, specifically on Friday at 5pm.

2. **Configure Schedule**: Set up the schedule as per your needs using the provided fields (e.g., `Weekly`, `Day of Week: Friday`, `Time: 17:00`).

## Exporting and Testing

1. **Save and Test**:
   - Save your workflow.
   - Trigger a test run to ensure everything is working correctly.

2. **Document Setup Instructions**: Write down the steps involved in setting up this workflow for others, including any variables that can be configured (GitHub repo, destination channel, language).

## Troubleshooting

- **API Rate Limiting**: Ensure you are not hitting rate limits by checking Claude's API documentation.
- **Authentication Issues**: Verify your credentials and ensure proper authentication is set up for both GitHub and Claude nodes.
- **Data Fetching Errors**: Check the logs to see if any data fetching issues occurred. Make sure the repository name or other filters are correctly configured.

## Conclusion

By following this tutorial, you will have created a robust automated workflow that generates weekly summaries of your GitHub repository's activity using n8n and Claude API. This setup not only saves time but also provides valuable insights into project progress and team collaboration.

### Additional Resources

- **n8n Documentation**: <https://docs.n8n.io/>
- **Claude API Documentation**: <https://docs.anthropic.com/>

## Summary of Workflow

1. **GitHub Node** - Fetches recent commits, closed issues, and merged pull requests.
2. **Claude AI Node** - Generates a narrative summary based on the fetched data.
3. **Email/Webhook Node** - Delivers the summary to your chosen destination.
4. **Schedule Node** - Ensures the workflow runs weekly.

By following these steps, you can create an automated system that keeps you informed about your project's progress every week!

---

This complete tutorial is designed to be clear and concise while providing detailed instructions for setting up the desired workflow with n8n and Claude API.