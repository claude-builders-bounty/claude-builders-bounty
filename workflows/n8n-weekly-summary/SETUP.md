# n8n Weekly Development Summary Workflow

Generates a weekly narrative summary of GitHub repo activity using Claude API.

## Setup

1. **Import** `n8n-workflow.json` into n8n (Settings → Import Workflow)
2. **Configure credentials**:
   - GitHub: Personal Access Token with repo scope
   - Claude API: API key from console.anthropic.com
   - Email: SMTP credentials (Gmail app password works)
3. **Set parameters** in the GitHub node:
   - Owner and repo to monitor
4. **Activate** the workflow

## What It Does

- Trigger: Every Friday at 5 PM
- Fetches: Commits, closed issues, merged PRs from the past week
- Generates: Narrative summary via Claude Sonnet 4
- Delivers: Email to configured address

## Bounty

Issue #5 — $200 (powered by Opire)
