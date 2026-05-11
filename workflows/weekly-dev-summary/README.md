# n8n Weekly GitHub Dev Summary Workflow

This folder contains the importable workflow for **Issue #5**.

## Setup (5 steps)

1. In n8n, go to **Import from File** and import `workflow.json` from this folder.
2. Open node **Workflow Config** and set:
   - `githubOwner` (repo owner/org)
   - `githubRepo` (repo name)
   - `language` (`EN` or `FR`)
   - `claudeApiKey` (Claude API key)
   - `destinationWebhook` (Discord webhook URL)
3. Optional: set `githubToken` if the repo is private or to avoid strict API rate limits.
4. Click **Execute Workflow** once manually to confirm it returns a summary item.
5. Activate the workflow; it runs every Friday at 17:00 local workflow timezone.

## Delivery

The workflow sends summary text to the configured Discord webhook (`destinationWebhook`).

## Verification

- Confirm successful run in the n8n execution log.
- Attach a screenshot of a successful execution and sent message for bounty review.
- Optional local validation: `node -e "JSON.parse(require('fs').readFileSync('workflows/weekly-dev-summary/workflow.json','utf8')); console.log('workflow json is valid')"`
