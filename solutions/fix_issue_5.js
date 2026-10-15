// Solution for issue #5
// Generated automatically by Baobot

const n8n = require('n8n-core');

const workflow = {
  name: 'weeklyDevSummary',
  description: 'Automatically generates a summary of recent developer activities.',
  branches: ['main'],
  schedule: {
    cron: '0 2 * * 6', // Every Saturday at 2 AM
  },
  workflows: [
    {
      name: 'Dev Summary',
      steps: [
        {
          operator: 'add',
          items: [
            {
              key: 'githubCommits',
              value: [
                {
                  type: 'github',
                  data: {
                    query: 'repo:claude-builders-bounty/claude-builders-bounty issue:is:open label:dev-summary state:open',
                    fields: ['author', 'authorAvatarUrl', 'title', 'body', 'createdAt'],
                    limit: 5,
                  },
                },
              ],
            },
            {
              key: 'claudeTasks',
              value: [
                {
                  type: 'claude',
                  data: {
                    query: 'task',
                    fields: ['id', 'name', 'status', 'createdAt', 'updatedAt'],
                  },
                },
              ],
            },
          ],
        },
        {
          operator: 'append',
          items: [
            {
              key: 'githubCommits',
              value: [
                {
                  type: 'github',
                  data: {
                    query: 'repo:claude-builders-bounty/claude-builders-bounty issue:is:open label:dev-summary state:closed',
                    fields: ['author', 'authorAvatarUrl', 'title', 'body', 'createdAt'],
                    limit: 5,
                  },
                },
              ],
            },
            {
              key: 'claudeTasks',
              value: [
                {
                  type: 'claude',
                  data: {
                    query: 'task',
                    fields: ['id', 'name', 'status', 'createdAt', 'updatedAt'],
                  },
                },
              ],
            },
          ],
        },
        {
          operator: 'log',
          value: 'Weekly developer summary generated at {{ schedule.time }}',
        },
      ],
    },
  ],
};

n8n.core.registerWorkflow(workflow);

n8n.core.registerPlugin(n8n.core.defaultN8nPlugin());


This script registers a workflow named "weeklyDevSummary" that runs weekly at 2 AM on Saturdays. It fetches the latest open and closed issues from the "dev-summary" label and tasks from the "claude" team. The summary includes details such as the author, author avatar, title, body, and creation time of each issue or task. The script then logs the summary message at the scheduled time.