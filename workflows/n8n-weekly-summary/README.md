# n8n + Claude AI: Automated GitHub Weekly Dev Summary

An automated n8n workflow that generates a weekly narrative summary of GitHub repository activity using Claude API (`claude-sonnet-4-20250514`) and delivers formatted reports directly to Discord/Slack webhooks or email.

---

## Acceptance Criteria Checklist

- [x] **Exportable n8n workflow**: `github_weekly_summary.workflow.json` (importable into any n8n instance)
- [x] **Trigger**: Weekly cron (`0 17 * * 5` — Every Friday at 5:00 PM UTC)
- [x] **GitHub API Ingestion**: Fetches commits, closed issues, and merged PRs for the past 7 days in parallel
- [x] **Claude API Analysis**: Uses `claude-sonnet-4-20250514` to synthesize activity into an executive narrative summary
- [x] **Delivery**: Formatted Discord embed webhook (compatible with Slack webhooks & email)
- [x] **Configurable Variables**: `github_owner`, `github_repo`, `language` (EN/FR), `discord_url` in a single config node
- [x] **Setup in 5 steps or fewer**
- [x] **Tested & Validated**

---

## Setup Instructions (5 Steps)

### Step 1: Import the Workflow
Open your n8n dashboard, click **Add Workflow** (`+`) > **Import from File**, and select [`github_weekly_summary.workflow.json`](github_weekly_summary.workflow.json).

### Step 2: Add GitHub Token Credential
In n8n, navigate to **Credentials** > **Add Credential** > **Header Auth**:
- **Credential Name**: `GitHub Token`
- **Name**: `Authorization`
- **Value**: `Bearer <YOUR_GITHUB_PERSONAL_ACCESS_TOKEN>`

### Step 3: Add Anthropic API Key Credential
Create a second **Header Auth** credential for Claude:
- **Credential Name**: `Anthropic API Key`
- **Name**: `x-api-key`
- **Value**: `<YOUR_ANTHROPIC_API_KEY>`

### Step 4: Configure Variables
Click on the **Config Variables** node (node #2) and edit the four parameters:
```javascript
const GITHUB_OWNER  = 'vercel';           // GitHub organization or user
const GITHUB_REPO   = 'next.js';          // Repository name
const LANGUAGE      = 'EN';               // 'EN' for English or 'FR' for French
const DISCORD_URL   = 'https://discord.com/api/webhooks/...'; // Your webhook URL
```

### Step 5: Activate the Workflow
Toggle the workflow switch to **Active** in the top-right corner. The workflow will automatically run every Friday at 5:00 PM UTC, or click **Test Workflow** to trigger an immediate run.

---

## How It Works

```text
[Every Friday 5pm (Cron)]
        │
        ▼
[Config Variables (Repo, Channel, Language)]
        │
   ┌────┼────────────────────────┐
   ▼    ▼                        ▼
[Commits] [Closed Issues] [Merged Pull Requests]
   │    │                        │
   └────┼────────────────────────┘
        ▼
[Aggregate GitHub Data (7-day window)]
        │
        ▼
[Build Claude Narrative Prompt]
        │
        ▼
[Call Claude API (claude-sonnet-4-20250514)]
        │
        ▼
[Extract Summary & Format Embed]
        │
        ▼
[Deliver to Discord / Slack Webhook]
```

---

## Sample Delivered Report

```markdown
## Summary
This week saw key improvements to authentication resilience and API response caching across 14 commits and 3 merged PRs. Core contributor focus centered on reducing cold-start latency and hardening session validation.

## Merged Pull Requests
- #4081: feat(hooks): pre-tool-use hook to block destructive bash commands (by @thepros2014)
- #4080: feat(skills): add automated changelog generator (by @armorbreak001)

## Closed Issues
- #3: HOOK: Pre-tool-use hook that blocks destructive bash commands [bounty, security]
- #12: Investigate sporadic database lock timeouts under high concurrency

## Commits
- [73d4e30] feat(hooks): add pre-tool-use hook to block destructive bash commands
- [8704e99] feat(skills): changelog generator pure bash script

## Momentum
Strong development velocity heading into the release cycle with all critical security gates passing.
```
