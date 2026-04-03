# n8n + Claude Code: Automated Weekly Dev Summary

Automated weekly development summary using n8n workflows and Claude AI.

## What It Does
Every Monday at 9AM:
1. Fetches GitHub activity (PRs, issues, events)
2. Sends data to Claude for intelligent summarization
3. Posts structured summary to Slack

## Files
- `workflow.json` — n8n workflow definition (import directly)
- `setup.md` — Configuration and deployment guide

## Quick Start
```bash
# 1. Import workflow.json into n8n
# 2. Configure credentials (GitHub, Anthropic, Slack)
# 3. Set environment variables
# 4. Activate workflow
```

## Output Example
```
## Weekly Dev Summary (Apr 7, 2026)

### Merged PRs
- #754: Goal-based savings tracking (shaidshark)
- #755: Background job retry system (shaidshark)

### Open Issues
- #76: PII Export & Delete (GDPR) — $500 bounty

### Key Metrics
- 5 PRs merged, 2 open
- 3 issues opened, 7 closed

### Action Items
- Review #76 GDPR implementation
- CI failing on #1233 — needs attention
```
