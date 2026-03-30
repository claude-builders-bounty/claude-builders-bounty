

---

## Development Setup

### Prerequisites
- [n8n](https://n8n.io) (self-hosted or cloud)
- Node.js 18+
- GitHub account with API token
- Anthropic API key

### Quick Start

1. **Import the workflow**:
   - Open n8n → Workflows → Import from JSON
   - Paste the contents of `weekly-dev-summary.workflow.json`

2. **Configure environment variables**:
   Copy `.env.example` to `.env` and fill in your values:

   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Required variables**:
   - `GITHUB_TOKEN` — GitHub Personal Access Token (needs repo read access)
   - `ANTHROPIC_API_KEY` — Anthropic API key for Claude
   - `GITHUB_OWNER` / `GITHUB_REPO` — Target repository

4. **Optional delivery channels**:
   - `DISCORD_WEBHOOK` — Discord webhook URL for instant delivery
   - `SMTP_*` — SMTP credentials for email delivery

5. **Test locally**:
   Trigger the workflow manually from n8n → Workflow → Test Workflow

6. **Connect to GitHub Action** (optional):
   The `.github/workflows/trigger-summary.yml` can be added to any repo to trigger this workflow on demand via a GitHub Action.

### Testing

```bash
# Validate JSON syntax
node -e "JSON.parse(require('fs').readFileSync('workflows/issue-5/weekly-dev-summary.workflow.json'))"
```

### Troubleshooting

- **Empty commits**: Check that `GITHUB_TOKEN` has repository access
- **Claude error**: Verify `ANTHROPIC_API_KEY` is valid
- **Discord not posting**: Ensure webhook URL is correct and accessible
