# 🔄 n8n + Claude API: Automated Weekly Developer Summary

An exportable [n8n](https://n8n.io) workflow that automatically compiles GitHub activity (commits, closed issues, merged pull requests) over the past 7 days and uses Claude Sonnet (`claude-sonnet-4-20250514`) to generate and post a narrative developer digest every Friday.

---

## ⚡ Workflow Architecture

```
[Weekly Cron (Fri 5PM)] 
       │
       ▼
[Config Variables] ──► [Compute 7-Day Window]
                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
[Fetch Commits]      [Fetch Closed Issues]   [Fetch Merged PRs]
       │                      │                      │
       └──────────────────────┬──────────────────────┘
                              ▼
                 [Aggregate & Format Prompt]
                              │
                              ▼
                 [Call Claude API (Sonnet 4)]
                              │
                              ▼
                 [Deliver via Webhook (Discord/Slack)]
```

---

## 🚀 Setup Guide (5 Steps or Fewer)

1. **Import Workflow**:
   - Open your n8n workspace.
   - Go to **Workflows** → **Import from File...** and select [`workflow.json`](workflow.json).

2. **Configure Variables**:
   - Double-click the **Config Variables** node and fill in:
     - `GITHUB_OWNER`: Your GitHub username or organization (e.g. `facebook`).
     - `GITHUB_REPO`: Your repository name (e.g. `react`).
     - `WEBHOOK_URL`: Your Discord or Slack incoming webhook URL.
     - `LANGUAGE`: `EN` for English, or `FR` for French.
     - `ANTHROPIC_API_KEY`: Your Anthropic API key (`sk-ant-api03-...`).

3. **Verify Date Range & Permissions**:
   - For private GitHub repos, add an `Authorization: Bearer <GITHUB_PAT>` header in the three GitHub HTTP Request nodes.

4. **Test Run**:
   - Click **Test Workflow** in n8n. Verify the formatted summary posts to your webhook.

5. **Activate**:
   - Toggle the workflow switch to **Active**. It will automatically execute every Friday at 5:00 PM.

---

## 📋 Generated Output Sample

```markdown
📢 **Weekly Developer Summary for owner/repository**

### 🌟 Executive Summary
Over the past week, the team maintained strong development momentum with 14 merged pull requests, 8 closed issues, and 26 direct commits. Core engineering efforts were centered on upgrading authentication resilience and slashing API latency across key endpoints.

### 🚀 Key Features & Improvements
- **Single-Flight Token Refresh**: Added thread-safe token renewal mechanisms to eliminate cross-tab race conditions (`PR #128`).
- **Turbopack Build Optimization**: Reduced local startup times by 35% through cached bundle manifests (`PR #134`).

### 🐛 Bugs Resolved & Quality
- **Issue #89**: Fixed intermittent memory leak on long-lived WebSocket reconnections.
- **Issue #94**: Corrected pagination offset truncation when default page limits were omitted.

### 🔮 Outlook for Next Week
- Finalize Stripe webhook idempotent replay protection.
- Roll out beta access for organization-level team RBAC.
```

---

## 🧪 Automated Testing

```bash
python3 workflows/weekly-dev-summary/test_workflow.py
```
Output:
```
Ran 5 tests in 0.001s
OK
```
