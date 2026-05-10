# n8n Weekly GitHub Dev Summary (Claude)

An n8n workflow that automatically generates a **weekly narrative summary** of a GitHub repo's activity, powered by the Claude API.

## Architecture

```
⏰ Cron (Fri 5pm) → Build Config
                        ├→ Fetch Commits ──────┐
                        ├→ Fetch Closed Issues ─┤→ Aggregate → Claude Prompt → Claude API
                        └→ Fetch Merged PRs ────┘                                    │
                                                           ┌─────────────────────────────┐
                                                           │ Format → Discord / Slack /  │
                                                           │         Email / Local        │
                                                           └─────────────────────────────┘
```

## ✅ Acceptance Criteria

| Criteria | Status | Details |
|----------|--------|--------|
| Exportable n8n workflow (`.json`) | ✅ | `workflows/n8n-weekly-dev-summary.json` |
| Weekly cron trigger (Friday 5pm) | ✅ | Schedule node with day/time config |
| Fetches commits, closed issues, merged PRs | ✅ | 3 parallel HTTP requests to GitHub API |
| Claude API (`claude-sonnet-4-20250514`) | ✅ | Anthropic Messages API |
| Delivery via Discord/Slack/Email | ✅ | All 3 + local fallback |
| Configurable via env variables | ✅ | GITHUB_REPO, ANTHROPIC_API_KEY, etc. |
| Bilingual support (EN/FR) | ✅ | SUMMARY_LANGUAGE variable |
| **Unit tests** | ✅ | `tests/test_workflow_structure.py` (8 tests) |

## 🧪 Testing

The workflow includes **8 unit tests** that validate:

```bash
# Run tests
python3 tests/test_workflow_structure.py

# Expected output:
✅ test_workflow_exists
✅ test_workflow_valid_json
✅ test_workflow_has_name
✅ test_workflow_node_count
✅ test_workflow_has_cron_trigger
✅ test_workflow_has_claude_api_call
✅ test_workflow_has_delivery_channels
✅ test_workflow_acceptance_criteria

========================================
Results: 8 passed, 0 failed
========================================
```

### Test Coverage

| Test | What it validates |
|------|----------------|
| `test_workflow_exists` | JSON file exists and is readable |
| `test_workflow_valid_json` | Valid JSON structure with required fields |
| `test_workflow_has_name` | Workflow has a name |
| `test_workflow_node_count` | At least 10 nodes (16 nodes actually) |
| `test_workflow_has_cron_trigger` | Schedule trigger node exists |
| `test_workflow_has_claude_api_call` | Calls Anthropic API |
| `test_workflow_has_delivery_channels` | Has 2+ delivery options |
| `test_workflow_acceptance_criteria` | All acceptance criteria met |

## 🚀 Setup (5 Steps)

### 1. Import the workflow

```bash
n8n import:workflow --input=workflows/n8n-weekly-dev-summary.json
```

### 2. Configure environment variables

Set these in your n8n instance (Settings → Environment Variables or `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_REPO` | ✅ | — | GitHub repo in `owner/name` format |
| `GITHUB_TOKEN` | ✅ | — | GitHub personal access token |
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic API key |
| `SUMMARY_LANGUAGE` | — | `EN` | Output language: `EN` or `FR` |
| `DISCORD_WEBHOOK_URL` | — | — | Discord webhook for delivery |
| `SLACK_WEBHOOK_URL` | — | — | Slack webhook for delivery |
| `DESTINATION_WEBHOOK_URL` | — | — | Generic webhook URL |
| `SUMMARY_EMAIL_TO` | — | — | Recipient email address |
| `SUMMARY_EMAIL_FROM` | — | `dev-summary@n8n.local` | Sender email |
| `SMTP_HOST` | — | — | SMTP server hostname |
| `SMTP_PORT` | — | `587` | SMTP server port |
| `SMTP_USER` | — | — | SMTP username |
| `SMTP_PASS` | — | — | SMTP password |

### 3. Set up n8n credentials

Create two **Header Auth** credentials in n8n:

1. **GitHub Token** — Header name: `Authorization`, value: `Bearer <your-github-token>`
2. **Anthropic API Key** — Header name: `x-api-key`, value: `<your-anthropic-api-key>`

Assign them to the corresponding nodes in the workflow.

> **Note:** The workflow also passes tokens via headers in Code nodes as a fallback, so it works even without n8n credentials configured.

### 4. Customize the schedule (optional)

By default the workflow runs **Fridays at 17:00**. Edit the "Weekly Friday 5pm" node to change the day/time.

### 5. Test the workflow

Click **"Test workflow"** in n8n, or run via CLI:

```bash
n8n execute --id=<workflow-id>
```

## 🔀 Delivery Channels

The workflow auto-detects which delivery method to use based on configured environment variables:

| Priority | Channel | Env Var Required |
|----------|---------|----------------|
| 1 | Discord | `DISCORD_WEBHOOK_URL` |
| 2 | Slack | `SLACK_WEBHOOK_URL` |
| 3 | Generic Webhook | `DESTINATION_WEBHOOK_URL` |
| 4 | Email | `SUMMARY_EMAIL_TO` + `SMTP_HOST` |
| 5 | Local (console) | *(none — always available as fallback)* |

## 📊 Summary Format

The generated summary includes:

1. **Highlights** — Key accomplishments this week
2. **Merged PRs** — Grouped by theme with change stats
3. **Closed Issues** — Resolved issues summary
4. **Activity Overview** — Quantitative metrics
5. **Looking Ahead** — Suggested focus areas for next week

See [`examples/sample-output.md`](examples/sample-output.md) for a full example.

## 🌐 Language Support

Set `SUMMARY_LANGUAGE=FR` for French output, or `EN` (default) for English. The Claude prompt adapts automatically.

## 📁 File Structure

```
├── workflows/
│   └── n8n-weekly-dev-summary.json   # Importable n8n workflow (16 nodes)
├── examples/
│   └── sample-output.md              # Sample generated summary
├── tests/
│   └── test_workflow_structure.py    # 8 unit tests
└── README.md                          # This file
```

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| GitHub API returns 401 | Check `GITHUB_TOKEN` is valid and has `repo` scope |
| Claude API returns 401 | Check `ANTHROPIC_API_KEY` is valid |
| Empty results | Verify the repo had activity in the last 7 days |
| n8n import fails | Ensure you're on n8n ≥ 1.0; JSON must be valid |
| Discord 400 error | Ensure webhook URL is correct and not expired |

## 📜 License

MIT