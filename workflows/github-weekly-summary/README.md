# GitHub Weekly Dev Summary — n8n + Claude

Automated n8n workflow that generates a narrative weekly summary of GitHub repository activity using Claude Sonnet.

## What It Does

Every Friday at 5pm, the workflow:
1. **Fetches** from GitHub API: commits, closed issues, merged PRs for the week
2. **Aggregates** activity: stats, contributors, PR titles, issue closures
3. **Generates** a narrative summary using `claude-sonnet-4-20250514`
4. **Delivers** to Slack, Discord, or email (your choice)

## Setup — 5 Steps

### Step 1: Import the Workflow
- Download `github-weekly-summary.workflow.json`
- In n8n: **Settings → Import from File** → select the JSON
- The workflow will appear as "GitHub Weekly Dev Summary"

### Step 2: Set Configuration Variables
Open the **"Set Config & Date Range"** Code node and edit:
```javascript
const CONFIG = {
  GITHUB_OWNER: 'your-org',          // GitHub username or org
  GITHUB_REPO: 'your-repo',          // Repository name
  LANGUAGE: 'EN',                    // 'EN' or 'FR'
  DELIVERY_TYPE: 'slack',            // 'slack', 'discord', or 'email'
  SLACK_WEBHOOK: 'https://hooks.slack.com/services/...',
  DISCORD_WEBHOOK: 'https://discord.com/api/webhooks/...',
  EMAIL_TO: 'team@yourcompany.com'
};
```

### Step 3: Add GitHub API Credentials
- In n8n: **Settings → Credentials → New Credential → HTTP Header Auth**
- Name: `GitHub API`
- Header name: `Authorization`
- Header value: `token YOUR_GITHUB_TOKEN`
- Assign to: **Fetch Commits**, **Fetch Closed Issues**, **Fetch Merged PRs** nodes

### Step 4: Add Anthropic API Credentials
- **Settings → Credentials → New Credential → HTTP Header Auth**
- Name: `Anthropic API`
- Header name: `x-api-key`
- Header value: `sk-ant-YOUR_ANTHROPIC_KEY`
- Assign to: **Claude: Generate Narrative Summary** node

### Step 5: Activate
- Toggle **Active** on the workflow
- Test immediately: click **Execute Workflow** manually

## Workflow Architecture

```
Cron (Friday 5pm)
      │
      ▼
Config + Date Range
      │
   ┌──┴──┬──────────┐
   ▼     ▼          ▼
Commits Issues   Merged PRs
   │     │          │
   └──┬──┴──────────┘
      ▼
Aggregate GitHub Data
      │
      ▼
Claude Sonnet: Generate Narrative
      │
      ▼
Format Message
      │
  ┌───┼───┐
  ▼   ▼   ▼
Slack Disc Email
```

## Example Output

```
📊 Weekly Dev Summary: myorg/myrepo
Week of Jul 7 – Jul 11, 2026

**Week in Review**
This was a strong week for the team, focused on shipping the v2.1 authentication
refactor. The backend team landed 3 critical PRs while the frontend team closed
out 7 long-standing UI issues.

**Key Highlights**
- 🚀 Merged PR #247: Complete OAuth2 refresh token implementation
- 🐛 Closed 7 UI issues from the Q2 backlog
- 📈 34 commits from 4 contributors — highest commit volume this month
- ✅ All CI checks passing after 2 weeks of flaky tests

**Contributors**
Great week from @alice (15 commits), @bob (12 commits), @carol (5 commits), and @dave (2 commits).

**Looking Ahead**
The auth work sets up the permissions system for next week. Open PRs #251–253 are 
review-ready and should close the sprint.
```

## Supported Languages
- `EN` — English
- `FR` — French (full narrative in French)

## Tested On
- n8n Cloud v1.95.2
- n8n self-hosted v1.93.0
- Verified with: `claude-sonnet-4-20250514`
