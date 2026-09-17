# Weekly GitHub Dev Summary via n8n & Claude

> Complete, exportable n8n workflow that automatically compiles weekly repository activity (commits, closed issues, and merged PRs) and uses the Claude API to synthesize and dispatch an executive developer narrative summary every Friday at 5:00 PM.

## Architecture

```
[Weekly Cron: Fri 5PM]
          ↓
[Config Variables]
          ↓
[Calculate 7-Day Window]
          ↓
  ├── [Fetch GitHub Commits] ──┐
  ├── [Fetch Closed Issues]  ──┼──> [Aggregate Activity Data] ──> [Claude API] ──> [Discord / Slack Webhook]
  └── [Fetch Closed PRs]     ──┘
```

---

## ⚡ Setup in 5 Steps

1. **Import Workflow into n8n**:
   - In your n8n canvas, click `Add workflow` > `Import from File...` and select `weekly-dev-summary-workflow.json`.

2. **Configure Repository Variables**:
   - Double-click the **Configuration Variables** node and set:
     - `GITHUB_OWNER`: Your GitHub username or organization (e.g. `facebook`).
     - `GITHUB_REPO`: Your repository name (e.g. `react`).
     - `LANGUAGE`: Language output — set to `EN` (English) or `FR` (French).
     - `CLAUDE_MODEL`: Default `claude-3-7-sonnet-20250219` (or `claude-3-5-sonnet-20241022`).
     - `WEBHOOK_URL`: Your Discord or Slack incoming webhook endpoint.

3. **Set Anthropic API Key**:
   - Ensure the environment variable `ANTHROPIC_API_KEY` is set in your n8n environment, or enter your API key directly into the **Call Claude API** node header `x-api-key`.

4. **Test Run**:
   - Click **Test step** on the *Deliver via Webhook* node to run an instant dry-run with the past 7 days of repository data.

5. **Activate**:
   - Toggle the workflow state to **Active**. The schedule trigger will execute every Friday at 5:00 PM automatically.

---

## ⚙️ Configurable Parameters

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `GITHUB_OWNER` | Owner of the target repository | `Wawen22` |
| `GITHUB_REPO` | Target GitHub repository | `autoIncome` |
| `LANGUAGE` | Output language of the executive summary | `EN` or `FR` |
| `CLAUDE_MODEL` | Anthropic model identifier | `claude-3-7-sonnet-20250219` |
| `WEBHOOK_URL` | Discord or Slack webhook destination | `https://discord.com/api/webhooks/...` |

---

## 📄 Sample Output (English)

> ### 🚀 Executive Overview
> Over the past week, the team maintained strong momentum across core infrastructure and automated tooling. A total of 14 commits were integrated and 3 critical PRs were successfully merged, achieving key milestones for our autonomous pipeline without introducing regressions.
>
> ### 📦 Major Releases & Key Merges
> - **PR #4296**: Integrated opinionated production `CLAUDE.md` template for Next.js 15 App Router and SQLite SaaS.
> - **PR #4297**: Deployed dual-mode Keep a Changelog generator skill and POSIX bash script.
> - **PR #4298**: Hardened security with pre-tool-use hook blocking destructive bash and SQL operations.
>
> ### 🐛 Bug Fixes & Resolved Issues
> - **Issue #12**: Resolved reverse SSH socket timeouts by adding automated exponential backoff reconnection.
> - **Issue #8**: Purged simulation records from SQLite revenue analytics view.
>
> ### 💡 Team Velocity & Next Priorities
> Sprint velocity is tracking ahead of schedule. The immediate priority is completing end-to-end webhook integration tests and finalizing documentation.
