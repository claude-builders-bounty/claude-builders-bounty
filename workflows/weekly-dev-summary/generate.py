#!/usr/bin/env python3
"""Generate n8n workflow JSON for weekly dev summary."""
import json
import sys

# Unique IDs for each node
CRON_ID = "1c3b4a5d-6e7f-8a9b-0c1d-2e3f4a5b6c7d"
GITHUB_COMMITS_ID = "2a3b4c5d-6e7f-8a9b-0c1d-2e3f4a5b6c7e"
GITHUB_ISSUES_ID = "3a4b5c6d-7e8f-9a0b-1c2d-3e4f5a6b7c8f"
GITHUB_PRS_ID = "4a5b6c7d-8e9f-0a1b-2c3d-4e5f6a7b8c9d"
FORMAT_DATE_ID = "5a6b7c8d-9e0f-1a2b-3c4d-5e6f7a8b9c0e"
MERGE_DATA_ID = "6a7b8c9d-0e1f-2a3b-4c5d-6e7f8a9b0c1f"
CLAUDE_API_ID = "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d"
OUTPUT_ID = "8a9b0c1d-2e3f-4a5b-6c7d-8e9f0a1b2c3d"

workflow = {
    "name": "Weekly Dev Summary",
    "nodes": [
        {
            "id": CRON_ID,
            "name": "Weekly Cron Trigger",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.1,
            "position": [250, 300],
            "parameters": {
                "rule": {
                    "interval": [{"item": [{"field": "cronExpression", "expression": "0 17 * * 5"}]}]
                }
            }
        },
        {
            "id": GITHUB_COMMITS_ID,
            "name": "Fetch Commits",
            "type": "n8n-nodes-base.github",
            "typeVersion": 2,
            "position": [500, 100],
            "parameters": {
                "resource": "repository",
                "operation": "listCommits",
                "owner": "={{ $json.owner || $env.GITHUB_OWNER }}",
                "repository": "={{ $json.repo || $env.GITHUB_REPO }}",
                "since": "={{ $json.since || $now.ago(7, 'days').toISO() }}",
                "until": "={{ $now.toISO() }}",
                "options": {}
            },
            "credentials": {
                "githubApi": "{{ $credentials }}"
            }
        },
        {
            "id": GITHUB_ISSUES_ID,
            "name": "Fetch Closed Issues",
            "type": "n8n-nodes-base.github",
            "typeVersion": 2,
            "position": [500, 300],
            "parameters": {
                "resource": "issue",
                "operation": "list",
                "owner": "={{ $json.owner || $env.GITHUB_OWNER }}",
                "repository": "={{ $json.repo || $env.GITHUB_REPO }}",
                "filters": {
                    "state": "closed",
                    "since": "={{ $json.since || $now.ago(7, 'days').toISO() }}"
                },
                "limit": 50
            },
            "credentials": {
                "githubApi": "{{ $credentials }}"
            }
        },
        {
            "id": GITHUB_PRS_ID,
            "name": "Fetch Merged PRs",
            "type": "n8n-nodes-base.github",
            "typeVersion": 2,
            "position": [500, 500],
            "parameters": {
                "resource": "pullRequest",
                "operation": "list",
                "owner": "={{ $json.owner || $env.GITHUB_OWNER }}",
                "repository": "={{ $json.repo || $env.GITHUB_REPO }}",
                "filters": {
                    "state": "closed",
                    "sort": "updated"
                },
                "limit": 50
            },
            "credentials": {
                "githubApi": "{{ $credentials }}"
            }
        },
        {
            "id": FORMAT_DATE_ID,
            "name": "Format Date Range",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.1,
            "position": [500, 700],
            "parameters": {
                "values": {
                    "string": [
                        {
                            "name": "since",
                            "value": "={{ $now.ago(7, 'days').format('yyyy-MM-dd') }}"
                        },
                        {
                            "name": "until",
                            "value": "={{ $now.format('yyyy-MM-dd') }}"
                        },
                        {
                            "name": "repo",
                            "value": "={{ $env.GITHUB_REPO }}"
                        },
                        {
                            "name": "language",
                            "value": "={{ $env.SUMMARY_LANGUAGE || 'EN' }}"
                        }
                    ]
                },
                "options": {}
            }
        },
        {
            "id": MERGE_DATA_ID,
            "name": "Merge Data",
            "type": "n8n-nodes-base.merge",
            "typeVersion": 2,
            "position": [750, 400],
            "parameters": {
                "mode": "combine",
                "combinationMode": "mergeByPosition"
            }
        },
        {
            "id": CLAUDE_API_ID,
            "name": "Claude API - Generate Summary",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [1000, 400],
            "parameters": {
                "method": "POST",
                "url": "https://api.anthropic.com/v1/messages",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpHeaderAuth",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "x-api-key", "value": "={{ $credentials.httpHeaderAuth.password }}"},
                        {"name": "anthropic-version", "value": "2023-06-01"},
                        {"name": "content-type", "value": "application/json"}
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {"name": "model", "value": "claude-sonnet-4-20250514"},
                        {"name": "max_tokens", "value": 2048},
                        {"name": "messages", "value": json.dumps([
                            {
                                "role": "user",
                                "content": f"""Generate a weekly dev summary for the repository.

Date Range: {{{{ $json.since }}}} to {{{{ $json.until }}}}
Language: {{{{ $json.language }}}}

Commits this week:
{{{{ JSON.stringify($json.commits).slice(0, 5000) }}}}

Closed Issues this week:
{{{{ JSON.stringify($json.issues).slice(0, 3000) }}}}

Merged PRs this week:
{{{{ JSON.stringify($json.prs).slice(0, 3000) }}}}

Format the summary with these sections:
## 📊 Weekly Dev Summary
### 📝 Commits
### ✅ Closed Issues  
### 🚀 Merged PRs
### 🎯 Key Highlights
### ⚠️ Items to Watch

Keep it concise and narrative-style.
"""}
                        ])}
                    ]
                },
                "options": {
                    "timeout": 120000
                }
            },
            "credentials": {
                "httpHeaderAuth": "{{ $credentials.claudeApiKey }}"
            }
        },
        {
            "id": OUTPUT_ID,
            "name": "Send Summary",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [1250, 400],
            "parameters": {
                "method": "POST",
                "path": "webhook-summary",
                "options": {},
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {"name": "summary", "value": "={{ $json.content }}"}
                    ]
                }
            }
        }
    ],
    "connections": {
        "Weekly Cron Trigger": {
            "main": [[{"node": "Fetch Commits", "type": "main", "index": 0}]]
        },
        "Weekly Cron Trigger": {
            "main": [[{"node": "Fetch Closed Issues", "type": "main", "index": 0}]]
        },
        "Weekly Cron Trigger": {
            "main": [[{"node": "Fetch Merged PRs", "type": "main", "index": 0}]]
        },
        "Weekly Cron Trigger": {
            "main": [[{"node": "Format Date Range", "type": "main", "index": 0}]]
        },
        "Fetch Commits": {
            "main": [[{"node": "Merge Data", "type": "main", "index": 0}]]
        },
        "Fetch Closed Issues": {
            "main": [[{"node": "Merge Data", "type": "main", "index": 1}]]
        },
        "Fetch Merged PRs": {
            "main": [[{"node": "Merge Data", "type": "main", "index": 2}]]
        },
        "Format Date Range": {
            "main": [[{"node": "Merge Data", "type": "main", "index": 3}]]
        },
        "Merge Data": {
            "main": [[{"node": "Claude API - Generate Summary", "type": "main", "index": 0}]]
        },
        "Claude API - Generate Summary": {
            "main": [[{"node": "Send Summary", "type": "main", "index": 0}]]
        }
    }
}

# Fix: ScheduleTrigger can only have one output connection
# We need to use a "Merge" node to split
workflow["nodes"].append({
    "id": "split-" + CRON_ID,
    "name": "Broadcast Trigger",
    "type": "n8n-nodes-base.merge",
    "typeVersion": 2,
    "position": [500, 400],
    "parameters": {
        "mode": "combine",
        "combinationMode": "mergeByPosition"
    }
})

# Fix connections - cron -> broadcast -> everyone
workflow["connections"]["Weekly Cron Trigger"] = {
    "main": [[{"node": "Broadcast Trigger", "type": "main", "index": 0}]]
}

workflow["connections"]["Broadcast Trigger"] = {
    "main": [
        [{"node": "Fetch Commits", "type": "main", "index": 0}],
        [{"node": "Fetch Closed Issues", "type": "main", "index": 0}],
        [{"node": "Fetch Merged PRs", "type": "main", "index": 0}],
        [{"node": "Format Date Range", "type": "main", "index": 0}]
    ]
}

with open("weekly-dev-summary.json", "w") as f:
    json.dump(workflow, f, indent=2)

print("✅ n8n workflow generated: weekly-dev-summary.json")
print(f"   Nodes: {len(workflow['nodes'])}")
