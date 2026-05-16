# n8n Claude Weekly Dev Summary

This package contains a tested n8n workflow that automatically generates weekly narrative summaries of GitHub repo activity using Claude API.

## Tested Environment

- **n8n Version:** 2.13.4
- **Test Method:** Started local n8n instance (`n8n start` on localhost:5678)
- **Workflow Status:** Successfully imported and validated

## Files

| File | Description |
|------|-------------|
| `workflows/weekly-dev-summary.json` | Complete n8n workflow (importable) |
| `README.md` | Full setup and usage documentation |

## Quick Start

```bash
# 1. Install n8n
npm install -g n8n

# 2. Start n8n
n8n start

# 3. Import workflow
# Open http://localhost:5678 → Workflows → Import from File → Select weekly-dev-summary.json

# 4. Add credentials (GitHub + Anthropic)
# 5. Configure env vars (repo, Discord webhook, language)
# 6. Activate workflow
```

## Workflow Features

- ✅ Weekly cron trigger
- ✅ Fetches commits, closed issues, merged PRs
- ✅ Claude API narrative generation
- ✅ Discord webhook delivery
- ✅ Configurable: repo, channel, language

## Screenshot

See [README.md](README.md) for detailed screenshot description and testing instructions.

---
**For Claude Builders Bounty #5** | $200
