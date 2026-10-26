import json
import uuid

def make_uuid():
    return str(uuid.uuid4())

nodes = [
    {
        "parameters": {
            "rule": {
                "interval": [
                    {
                        "field": "weeks",
                        "triggerAtDay": [5],
                        "triggerAtHour": 17,
                        "triggerAtMinute": 0
                    }
                ]
            }
        },
        "id": make_uuid(),
        "name": "Weekly Trigger (Friday 5PM)",
        "type": "n8n-nodes-base.scheduleTrigger",
        "typeVersion": 1.2,
        "position": [200, 300]
    },
    {
        "parameters": {
            "assignments": {
                "assignments": [
                    {
                        "id": make_uuid(),
                        "name": "repo_owner",
                        "value": "={{ $env.GITHUB_REPO_OWNER || 'BasedHardware' }}",
                        "type": "string"
                    },
                    {
                        "id": make_uuid(),
                        "name": "repo_name",
                        "value": "={{ $env.GITHUB_REPO_NAME || 'omi' }}",
                        "type": "string"
                    },
                    {
                        "id": make_uuid(),
                        "name": "summary_language",
                        "value": "={{ $env.SUMMARY_LANGUAGE || 'EN' }}",
                        "type": "string"
                    },
                    {
                        "id": make_uuid(),
                        "name": "delivery_channel",
                        "value": "={{ $env.DELIVERY_CHANNEL || 'slack' }}",
                        "type": "string"
                    },
                    {
                        "id": make_uuid(),
                        "name": "slack_webhook_url",
                        "value": "={{ $env.SLACK_WEBHOOK_URL || '' }}",
                        "type": "string"
                    },
                    {
                        "id": make_uuid(),
                        "name": "discord_webhook_url",
                        "value": "={{ $env.DISCORD_WEBHOOK_URL || '' }}",
                        "type": "string"
                    }
                ]
            },
            "options": {}
        },
        "id": make_uuid(),
        "name": "Config Variables",
        "type": "n8n-nodes-base.set",
        "typeVersion": 3.4,
        "position": [420, 300]
    },
    {
        "parameters": {
            "jsCode": """
const now = new Date();
const sevenDaysAgo = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
const sinceIso = sevenDaysAgo.toISOString();
const untilIso = now.toISOString();

return {
  ...$input.first().json,
  since_iso: sinceIso,
  until_iso: untilIso,
  start_date_str: sevenDaysAgo.toISOString().slice(0, 10),
  end_date_str: now.toISOString().slice(0, 10)
};
"""
        },
        "id": make_uuid(),
        "name": "Compute 7-Day Window",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [640, 300]
    },
    {
        "parameters": {
            "url": "=https://api.github.com/repos/{{ $json.repo_owner }}/{{ $json.repo_name }}/commits",
            "sendQuery": True,
            "queryParameters": {
                "parameters": [
                    {
                        "name": "since",
                        "value": "={{ $json.since_iso }}"
                    },
                    {
                        "name": "per_page",
                        "value": "100"
                    }
                ]
            },
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Accept",
                        "value": "application/vnd.github.v3+json"
                    },
                    {
                        "name": "User-Agent",
                        "value": "n8n-claude-weekly-summary"
                    },
                    {
                        "name": "Authorization",
                        "value": "={{ $env.GITHUB_TOKEN ? 'Bearer ' + $env.GITHUB_TOKEN : '' }}"
                    }
                ]
            },
            "options": {}
        },
        "id": make_uuid(),
        "name": "Fetch Commits",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [880, 180]
    },
    {
        "parameters": {
            "url": "=https://api.github.com/repos/{{ $('Compute 7-Day Window').first().json.repo_owner }}/{{ $('Compute 7-Day Window').first().json.repo_name }}/issues",
            "sendQuery": True,
            "queryParameters": {
                "parameters": [
                    {
                        "name": "state",
                        "value": "closed"
                    },
                    {
                        "name": "since",
                        "value": "={{ $('Compute 7-Day Window').first().json.since_iso }}"
                    },
                    {
                        "name": "per_page",
                        "value": "100"
                    }
                ]
            },
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Accept",
                        "value": "application/vnd.github.v3+json"
                    },
                    {
                        "name": "User-Agent",
                        "value": "n8n-claude-weekly-summary"
                    },
                    {
                        "name": "Authorization",
                        "value": "={{ $env.GITHUB_TOKEN ? 'Bearer ' + $env.GITHUB_TOKEN : '' }}"
                    }
                ]
            },
            "options": {}
        },
        "id": make_uuid(),
        "name": "Fetch Closed Issues",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [880, 300]
    },
    {
        "parameters": {
            "url": "=https://api.github.com/repos/{{ $('Compute 7-Day Window').first().json.repo_owner }}/{{ $('Compute 7-Day Window').first().json.repo_name }}/pulls",
            "sendQuery": True,
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
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Accept",
                        "value": "application/vnd.github.v3+json"
                    },
                    {
                        "name": "User-Agent",
                        "value": "n8n-claude-weekly-summary"
                    },
                    {
                        "name": "Authorization",
                        "value": "={{ $env.GITHUB_TOKEN ? 'Bearer ' + $env.GITHUB_TOKEN : '' }}"
                    }
                ]
            },
            "options": {}
        },
        "id": make_uuid(),
        "name": "Fetch Pull Requests",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [880, 420]
    },
    {
        "parameters": {
            "jsCode": """
const config = $('Compute 7-Day Window').first().json;
const sinceDate = new Date(config.since_iso);

// Process commits
const commitsRaw = $('Fetch Commits').all().map(i => i.json);
const commits = (Array.isArray(commitsRaw) ? commitsRaw : []).map(c => ({
  sha: (c.sha || '').slice(0, 7),
  author: c.commit?.author?.name || c.author?.login || 'Unknown',
  message: (c.commit?.message || '').split('\\n')[0],
  date: c.commit?.author?.date || ''
})).slice(0, 40);

// Process closed issues (filter out PRs returned by issues endpoint)
const issuesRaw = $('Fetch Closed Issues').all().map(i => i.json);
const closedIssues = (Array.isArray(issuesRaw) ? issuesRaw : [])
  .filter(iss => !iss.pull_request)
  .map(iss => ({
    number: iss.number,
    title: iss.title,
    author: iss.user?.login || 'Unknown',
    closed_at: iss.closed_at
  })).slice(0, 30);

// Process merged PRs in the last 7 days
const pullsRaw = $('Fetch Pull Requests').all().map(i => i.json);
const mergedPulls = (Array.isArray(pullsRaw) ? pullsRaw : [])
  .filter(pr => pr.merged_at && new Date(pr.merged_at) >= sinceDate)
  .map(pr => ({
    number: pr.number,
    title: pr.title,
    author: pr.user?.login || 'Unknown',
    merged_at: pr.merged_at
  })).slice(0, 30);

const language = (config.summary_language || 'EN').toUpperCase();
const langInstruction = language === 'FR' 
  ? 'Rédige le résumé hebdomadaire entièrement en FRANÇAIS, avec un ton professionnel et engageant.' 
  : 'Write the weekly developer summary entirely in ENGLISH, with a professional and engaging tone.';

const prompt = `You are Claude Code, an expert technical lead and developer relations engineer.
Generate an engaging, narrative weekly developer activity summary for the repository: ${config.repo_owner}/${config.repo_name}.
Period: ${config.start_date_str} to ${config.end_date_str}.

${langInstruction}

Here is the raw activity data from the past 7 days:

Merged Pull Requests (${mergedPulls.length}):
${mergedPulls.map(p => `- #${p.number}: ${p.title} (by @${p.author})`).join('\\n') || 'None this week.'}

Closed Issues Resolved (${closedIssues.length}):
${closedIssues.map(i => `- #${i.number}: ${i.title}`).join('\\n') || 'None this week.'}

Recent Commits (${commits.length}):
${commits.slice(0, 25).map(c => `- [${c.sha}] ${c.message} (${c.author})`).join('\\n') || 'None recorded.'}

Structure the summary cleanly using Markdown:
1. **Executive Narrative**: A 2-3 paragraph overview capturing the high-level progress, architectural focus, and engineering momentum.
2. **Key Shipped Features & Enhancements**: Detailed bullet points highlighting merged PRs and core improvements.
3. **Resolved Issues & Quality Fixes**: Breakdown of closed issues and bug remediations.
4. **Contributor Spotlight**: Shout-out to contributors who landed PRs and fixes this week.

Keep it concise, technically accurate, and readable for both technical contributors and leadership.`;

return {
  ...config,
  commits_count: commits.length,
  closed_issues_count: closedIssues.length,
  merged_prs_count: mergedPulls.length,
  prompt: prompt
};
"""
        },
        "id": make_uuid(),
        "name": "Aggregate & Format Prompt",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1120, 300]
    },
    {
        "parameters": {
            "method": "POST",
            "url": "https://api.anthropic.com/v1/messages",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "x-api-key",
                        "value": "={{ $env.ANTHROPIC_API_KEY }}"
                    },
                    {
                        "name": "anthropic-version",
                        "value": "2023-06-01"
                    },
                    {
                        "name": "content-type",
                        "value": "application/json"
                    }
                ]
            },
            "sendBody": True,
            "bodyParameters": {
                "parameters": []
            },
            "specifyBody": "json",
            "jsonBody": "={\\n  \"model\": \"claude-3-5-sonnet-20241022\",\\n  \"max_tokens\": 2048,\\n  \"messages\": [\\n    {\\n      \"role\": \"user\",\\n      \"content\": {{ JSON.stringify($json.prompt) }}\\n    }\\n  ]\\n}",
            "options": {}
        },
        "id": make_uuid(),
        "name": "Call Claude API",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [1360, 300]
    },
    {
        "parameters": {
            "jsCode": """
const response = $input.first().json;
const contentList = response.content || [];
const summaryText = contentList.filter(c => c.type === 'text').map(c => c.text).join('\\n\\n');

const agg = $('Aggregate & Format Prompt').first().json;

return {
  repo_owner: agg.repo_owner,
  repo_name: agg.repo_name,
  start_date_str: agg.start_date_str,
  end_date_str: agg.end_date_str,
  delivery_channel: (agg.delivery_channel || 'slack').toLowerCase(),
  slack_webhook_url: agg.slack_webhook_url,
  discord_webhook_url: agg.discord_webhook_url,
  summary: summaryText,
  commits_count: agg.commits_count,
  closed_issues_count: agg.closed_issues_count,
  merged_prs_count: agg.merged_prs_count
};
"""
        },
        "id": make_uuid(),
        "name": "Parse Claude Output",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1580, 300]
    },
    {
        "parameters": {
            "dataType": "string",
            "value1": "={{ $json.delivery_channel }}",
            "rules": {
                "rules": [
                    {
                        "value2": "slack",
                        "output": 0
                    },
                    {
                        "value2": "discord",
                        "output": 1
                    }
                ]
            },
            "fallbackOutput": 0
        },
        "id": make_uuid(),
        "name": "Route Delivery Channel",
        "type": "n8n-nodes-base.switch",
        "typeVersion": 2,
        "position": [1800, 300]
    },
    {
        "parameters": {
            "method": "POST",
            "url": "={{ $json.slack_webhook_url }}",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Content-Type",
                        "value": "application/json"
                    }
                ]
            },
            "specifyBody": "json",
            "jsonBody": "={\\n  \"text\": \"*Weekly Dev Summary: \" + $json.repo_owner + \"/\" + $json.repo_name + \"*\\n\\n\" + $json.summary\\n}",
            "options": {}
        },
        "id": make_uuid(),
        "name": "Deliver via Slack Webhook",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [2060, 220]
    },
    {
        "parameters": {
            "method": "POST",
            "url": "={{ $json.discord_webhook_url }}",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Content-Type",
                        "value": "application/json"
                    }
                ]
            },
            "specifyBody": "json",
            "jsonBody": "={\\n  \"content\": \"**Weekly Dev Summary: \" + $json.repo_owner + \"/\" + $json.repo_name + \"**\\n\\n\" + $json.summary.slice(0, 1900)\\n}",
            "options": {}
        },
        "id": make_uuid(),
        "name": "Deliver via Discord Webhook",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [2060, 380]
    }
]

connections = {
    "Weekly Trigger (Friday 5PM)": {
        "main": [
            [
                {
                    "node": "Config Variables",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Config Variables": {
        "main": [
            [
                {
                    "node": "Compute 7-Day Window",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Compute 7-Day Window": {
        "main": [
            [
                {
                    "node": "Fetch Commits",
                    "type": "main",
                    "index": 0
                },
                {
                    "node": "Fetch Closed Issues",
                    "type": "main",
                    "index": 0
                },
                {
                    "node": "Fetch Pull Requests",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Fetch Commits": {
        "main": [
            [
                {
                    "node": "Aggregate & Format Prompt",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Fetch Closed Issues": {
        "main": [
            [
                {
                    "node": "Aggregate & Format Prompt",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Fetch Pull Requests": {
        "main": [
            [
                {
                    "node": "Aggregate & Format Prompt",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Aggregate & Format Prompt": {
        "main": [
            [
                {
                    "node": "Call Claude API",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Call Claude API": {
        "main": [
            [
                {
                    "node": "Parse Claude Output",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Parse Claude Output": {
        "main": [
            [
                {
                    "node": "Route Delivery Channel",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Route Delivery Channel": {
        "main": [
            [
                {
                    "node": "Deliver via Slack Webhook",
                    "type": "main",
                    "index": 0
                }
            ],
            [
                {
                    "node": "Deliver via Discord Webhook",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    }
}

workflow = {
    "name": "Weekly Dev Summary with Claude & GitHub",
    "nodes": nodes,
    "connections": connections,
    "pinData": {},
    "settings": {
        "executionOrder": "v1"
    },
    "versionId": make_uuid(),
    "meta": {
        "templateCredsSetupCompleted": True,
        "instanceId": "claude-builders-n8n-workflow-v1"
    }
}

target_path = r"D:\projects\claude-builders-bounty\workflows\n8n-weekly-summary\workflow.json"
with open(target_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(workflow, f, indent=2)

print(f"Generated n8n workflow JSON at {target_path} successfully ({len(nodes)} nodes).")
