# Weekly Report Workflow — n8n + Claude API

Automated weekly report generation using n8n and Claude API.

## Setup
1. Import `workflow.json` into n8n
2. Set environment variables: `DATA_SOURCE_URL`, `REPORT_EMAIL`, `ANTHROPIC_API_KEY`
3. Activate the workflow

## How it works
- Triggers every Monday at 9am
- Fetches data from your data source
- Sends to Claude for summarization
- Emails the report
