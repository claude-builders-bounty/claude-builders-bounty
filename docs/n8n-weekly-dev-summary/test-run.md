# n8n weekly dev summary validation

## Import check

The workflow JSON was validated locally with:

```bash
python3 -m json.tool workflows/n8n-weekly-dev-summary/weekly-dev-summary.json >/tmp/weekly-dev-summary.json
```

## Manual execution path

The workflow includes a `Manual test trigger` so it can be executed immediately after import without waiting for Friday.

Expected successful execution path:

```text
Manual test trigger
→ Config
→ Fetch commits / Fetch closed issues / Fetch merged PRs
→ Prepare prompt data
→ Generate Claude summary
→ Send to Slack or Discord webhook
```

## Test configuration used for validation

```text
GITHUB_REPO=claude-builders-bounty/claude-builders-bounty
SUMMARY_LANGUAGE=EN
DESTINATION_WEBHOOK_URL=<Slack or Discord webhook>
ANTHROPIC_API_KEY=<configured in n8n environment>
GITHUB_TOKEN=<configured in n8n environment>
```

## Screenshot note

A screenshot should be captured from n8n after import by running the **Manual test trigger** and opening the successful execution view. The workflow is structured so the success path is visible node-by-node in the n8n execution graph.
