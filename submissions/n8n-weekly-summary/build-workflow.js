const fs = require('fs');
const path = require('path');

const readNodeCode = (filename) => {
  return fs.readFileSync(path.join(__dirname, 'nodes', filename), 'utf8');
};

const workflowConfigJs = readNodeCode('workflow-config.js');
const aggregateDigestJs = readNodeCode('aggregate-digest.js');
const formatPayloadJs = readNodeCode('format-payload.js');

const workflow = {
  "name": "Claude Code - Automated Weekly Dev Summary",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "cronExpression",
              "expression": "0 17 * * 5"
            }
          ]
        }
      },
      "id": "trigger-weekly-cron",
      "name": "Weekly Trigger (Cron)",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.2,
      "position": [120, 240]
    },
    {
      "parameters": {},
      "id": "trigger-manual-run",
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [120, 440]
    },
    {
      "parameters": {
        "jsCode": workflowConfigJs
      },
      "id": "node-workflow-config",
      "name": "Workflow Configuration",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [340, 340]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "=https://api.github.com/repos/{{ $('Workflow Configuration').item.json.githubOwner }}/{{ $('Workflow Configuration').item.json.githubRepo }}/commits",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Accept",
              "value": "application/vnd.github.v3+json"
            },
            {
              "name": "User-Agent",
              "value": "n8n-Claude-Dev-Summary"
            },
            {
              "name": "Authorization",
              "value": "={{ $('Workflow Configuration').item.json.githubToken ? 'Bearer ' + $('Workflow Configuration').item.json.githubToken : undefined }}"
            }
          ]
        },
        "sendQuery": true,
        "queryParameters": {
          "parameters": [
            {
              "name": "since",
              "value": "={{ $('Workflow Configuration').item.json.sinceISO }}"
            },
            {
              "name": "per_page",
              "value": "100"
            }
          ]
        },
        "options": {
          "response": {
            "response": {
              "neverError": true
            }
          }
        }
      },
      "id": "node-github-commits",
      "name": "GitHub Commits",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [600, 160],
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "method": "GET",
        "url": "=https://api.github.com/repos/{{ $('Workflow Configuration').item.json.githubOwner }}/{{ $('Workflow Configuration').item.json.githubRepo }}/issues",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Accept",
              "value": "application/vnd.github.v3+json"
            },
            {
              "name": "User-Agent",
              "value": "n8n-Claude-Dev-Summary"
            },
            {
              "name": "Authorization",
              "value": "={{ $('Workflow Configuration').item.json.githubToken ? 'Bearer ' + $('Workflow Configuration').item.json.githubToken : undefined }}"
            }
          ]
        },
        "sendQuery": true,
        "queryParameters": {
          "parameters": [
            {
              "name": "state",
              "value": "closed"
            },
            {
              "name": "since",
              "value": "={{ $('Workflow Configuration').item.json.sinceISO }}"
            },
            {
              "name": "per_page",
              "value": "100"
            }
          ]
        },
        "options": {
          "response": {
            "response": {
              "neverError": true
            }
          }
        }
      },
      "id": "node-github-issues",
      "name": "GitHub Issues",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [600, 340],
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "method": "GET",
        "url": "=https://api.github.com/repos/{{ $('Workflow Configuration').item.json.githubOwner }}/{{ $('Workflow Configuration').item.json.githubRepo }}/pulls",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Accept",
              "value": "application/vnd.github.v3+json"
            },
            {
              "name": "User-Agent",
              "value": "n8n-Claude-Dev-Summary"
            },
            {
              "name": "Authorization",
              "value": "={{ $('Workflow Configuration').item.json.githubToken ? 'Bearer ' + $('Workflow Configuration').item.json.githubToken : undefined }}"
            }
          ]
        },
        "sendQuery": true,
        "queryParameters": {
          "parameters": [
            {
              "name": "state",
              "value": "closed"
            },
            {
              "name": "sort",
              "value": "updated"
            },
            {
              "name": "direction",
              "value": "desc"
            },
            {
              "name": "per_page",
              "value": "100"
            }
          ]
        },
        "options": {
          "response": {
            "response": {
              "neverError": true
            }
          }
        }
      },
      "id": "node-github-prs",
      "name": "GitHub Merged PRs",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [600, 520],
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "jsCode": aggregateDigestJs
      },
      "id": "node-aggregate-digest",
      "name": "Aggregate Activity Digest",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [860, 340]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://api.anthropic.com/v1/messages",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "anthropic-version",
              "value": "2023-06-01"
            },
            {
              "name": "content-type",
              "value": "application/json"
            },
            {
              "name": "x-api-key",
              "value": "={{ $json.anthropicApiKey }}"
            }
          ]
        },
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({\n  model: $json.claudeModel || 'claude-sonnet-4-20250514',\n  max_tokens: 2500,\n  system: $json.systemPrompt,\n  messages: [\n    { role: 'user', content: $json.userPrompt }\n  ]\n}) }}",
        "options": {
          "response": {
            "response": {
              "neverError": true
            }
          }
        }
      },
      "id": "node-claude-summary",
      "name": "Claude Sonnet 4 Summary",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [1120, 340],
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "jsCode": formatPayloadJs
      },
      "id": "node-format-payload",
      "name": "Format Payload",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1360, 340]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $json.discordWebhookUrl || 'https://httpbin.org/status/200' }}",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.discordPayload) }}",
        "options": {
          "response": {
            "response": {
              "neverError": true
            }
          }
        }
      },
      "id": "node-send-discord",
      "name": "Send Discord Webhook",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [1620, 220],
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $json.slackWebhookUrl || 'https://httpbin.org/status/200' }}",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.slackPayload) }}",
        "options": {
          "response": {
            "response": {
              "neverError": true
            }
          }
        }
      },
      "id": "node-send-slack",
      "name": "Send Slack Webhook",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [1620, 460],
      "onError": "continueRegularOutput"
    }
  ],
  "connections": {
    "Weekly Trigger (Cron)": {
      "main": [
        [
          {
            "node": "Workflow Configuration",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Manual Trigger": {
      "main": [
        [
          {
            "node": "Workflow Configuration",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Workflow Configuration": {
      "main": [
        [
          {
            "node": "GitHub Commits",
            "type": "main",
            "index": 0
          },
          {
            "node": "GitHub Issues",
            "type": "main",
            "index": 0
          },
          {
            "node": "GitHub Merged PRs",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "GitHub Commits": {
      "main": [
        [
          {
            "node": "Aggregate Activity Digest",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "GitHub Issues": {
      "main": [
        [
          {
            "node": "Aggregate Activity Digest",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "GitHub Merged PRs": {
      "main": [
        [
          {
            "node": "Aggregate Activity Digest",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Aggregate Activity Digest": {
      "main": [
        [
          {
            "node": "Claude Sonnet 4 Summary",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Claude Sonnet 4 Summary": {
      "main": [
        [
          {
            "node": "Format Payload",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Format Payload": {
      "main": [
        [
          {
            "node": "Send Discord Webhook",
            "type": "main",
            "index": 0
          },
          {
            "node": "Send Slack Webhook",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "settings": {
    "executionOrder": "v1"
  },
  "staticData": null,
  "meta": {
    "instanceId": "claude-code-weekly-dev-summary"
  },
  "tags": [
    {
      "name": "Claude Code",
      "id": "claude-code"
    },
    {
      "name": "GitHub",
      "id": "github"
    },
    {
      "name": "Weekly Digest",
      "id": "weekly-digest"
    }
  ],
  "active": false,
  "versionId": "1.0.0"
};

const outputPath = path.join(__dirname, 'n8n-claude-weekly-dev-summary.json');
fs.writeFileSync(outputPath, JSON.stringify(workflow, null, 2), 'utf-8');
console.log('✅ n8n-claude-weekly-dev-summary.json built successfully at ' + outputPath);
