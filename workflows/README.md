# Weekly GitHub Dev Summary — n8n + Claude

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using Claude AI.

## What It Does

Every Friday at 5pm, the workflow:
1. Fetches the last 7 days of commits, closed issues, and merged PRs from GitHub
2. Aggregates the activity into a structured data object
3. Sends it to Claude (Haiku) to write a 3-4 paragraph narrative summary
4. Outputs a formatted Markdown email-ready report

## Import Instructions

1. Open your n8n instance
2. Go to **Workflows → Import from file**
3. Upload `weekly_summary.workflow.json`
4. Configure credentials (see below)
5. Set `GITHUB_REPO` environment variable or edit the "Set Date Range" node

## Credentials Required

### GitHub Token
- Create at: https://github.com/settings/tokens/new
- Scopes needed: `repo` (read)
- In n8n: **Credentials → HTTP Header Auth**
  - Name: `GitHub Token`
  - Header: `Authorization`  
  - Value: `Bearer ghp_your_token_here`

### Anthropic API Key
- Get at: https://console.anthropic.com
- In n8n: **Credentials → HTTP Header Auth**
  - Name: `Anthropic API Key`
  - Header: `x-api-key`
  - Value: `sk-ant-...`

## Configuration

Edit the **Set Date Range** node to change:
- `GITHUB_REPO`: e.g. `"facebook/react"` (or set as n8n env variable)

Edit the **Every Friday 5pm** node to change the schedule.

## Output Example

```
Subject: Weekly Dev Summary — myorg/myapp (2026-05-28)

# Weekly Development Summary

**Repo:** myorg/myapp  
**Week ending:** 2026-05-28  
**Commits:** 23 | **Issues closed:** 8 | **PRs merged:** 6

---

This was a productive week for myapp, with the team landing 23 commits across 
6 pull requests. The headline change was the new payment retry logic in PR #142, 
which resolves a long-standing issue where failed Stripe charges weren't being 
retried correctly...
```

## Extending the Workflow

To send via email: add an **Email (SMTP)** node after "Format Output" using `{{ $json.subject }}` and `{{ $json.body }}`.

To send via Slack: add a **Slack** node with message `{{ $json.body }}`.
