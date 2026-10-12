# n8n + Claude Code: Automated Weekly Dev Summary

An automated, production-ready n8n workflow that triggers every Friday at 5:00 PM, fetches all commits, closed issues, and merged PRs for the trailing 7 days from the GitHub API, and generates a structured executive narrative summary using the Claude API (`claude-sonnet-4-20250514`), delivering it directly to your Discord or Slack channel.

---

## 5-Step Setup Guide

1. **Import the Workflow**
   - Open your n8n workspace.
   - Click **Add Workflow** > **Import from File...** and select [`weekly_dev_summary.json`](weekly_dev_summary.json).

2. **Configure Environment / Node Variables**
   - Double-click the **Configuration & Environment** node and set your variables (or export them as container environment variables):
     - `GITHUB_REPO_OWNER`: e.g. `facebook`
     - `GITHUB_REPO_NAME`: e.g. `react`
     - `DESTINATION_CHANNEL`: `discord` or `slack`
     - `SUMMARY_LANGUAGE`: `EN` or `FR`

3. **Set Secrets (Credentials)**
   - `ANTHROPIC_API_KEY`: Your Anthropic API key (`sk-ant-...`).
   - `GITHUB_TOKEN`: A GitHub Personal Access Token (optional for public repos, recommended to prevent rate limits).
   - `WEBHOOK_URL`: Your Discord or Slack incoming webhook URL.

4. **Test Run**
   - Click **Test step** on the *Configuration & Environment* node, followed by **Test Workflow**.
   - Verify the summary arrives in your target Slack or Discord channel.

5. **Activate the Schedule**
   - Toggle the workflow switch to **Active**.
   - The workflow will automatically run every Friday at 17:00 (5:00 PM) UTC.

---

## Configurable Variables Reference

| Variable | Description | Default | Allowed Values |
| :--- | :--- | :--- | :--- |
| `GITHUB_REPO_OWNER` | Repository owner/organization | `facebook` | Any valid GitHub org/user |
| `GITHUB_REPO_NAME` | Repository repository name | `react` | Any valid GitHub repository |
| `GITHUB_TOKEN` | GitHub PAT for authenticated API calls | `""` | `ghp_...` |
| `ANTHROPIC_API_KEY` | Claude API secret key | `""` | `sk-ant-...` |
| `DESTINATION_CHANNEL`| Target webhook formatting style | `discord` | `discord` \| `slack` |
| `WEBHOOK_URL` | Incoming webhook target endpoint | `""` | Valid HTTPS Webhook URL |
| `SUMMARY_LANGUAGE` | Language of the executive summary | `EN` | `EN` (English) \| `FR` (French) |

---

## Workflow Architecture

```
[Weekly Cron (Friday 5PM)]
          │
          ▼
[Configuration & Environment]
          │
          ▼
[Calculate 7-Day Window]
    ├───► [Fetch Weekly Commits]
    ├───► [Fetch Closed Issues]
    └───► [Fetch Closed PRs]
          │
          ▼
[Aggregate Activity & Prompt]
          │
          ▼
[Call Claude Sonnet (claude-sonnet-4-20250514)]
          │
          ▼
[Format Discord/Slack Payload]
          │
          ▼
[Deliver Webhook]
```

---

## Sample Outputs

### English (`EN`):
> 📢 **Weekly Engineering Summary: facebook/react (2026-10-05 to 2026-10-12)**
>
> **1. 🚀 Key Highlights & Major Milestones**
> The engineering team completed significant stabilization across concurrent rendering pipelines, closing 8 key issues and landing 12 pull requests.
>
> **2. 🛠️ Shipped Features & Bug Fixes**
> - Enhanced transition scheduling heuristics for nested Suspense boundaries.
> - Fixed memory retention bug in dev server hot module reloading.
>
> **3. 🎯 Next Week's Momentum & Engineering Focus**
> Next sprint prioritizes canary validation and optimizing server action payload serialization.

---

## Contract Verification

Run the test suite to verify n8n schema compatibility:
```bash
python -m unittest workflows/n8n-claude-weekly-summary/test_workflow.py
```
```
......
----------------------------------------------------------------------
Ran 6 tests in 0.001s

OK
```
