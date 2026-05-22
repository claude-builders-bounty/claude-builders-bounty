# Weekly GitHub Dev Summary — n8n + Claude

An importable n8n workflow that, every Friday at 5pm, fetches the last week's GitHub activity (commits, merged PRs, closed issues), asks Claude to write a narrative summary, and emails it.

## Setup (5 steps)

```bash
# 1. Install n8n (one-time)
npx n8n
# Opens at http://localhost:5678 — create your local account when prompted.

# 2. Import the workflow
# In the n8n UI: top-right menu -> "Import from File" -> select weekly-dev-summary.json
```

3. **Edit the `Config (edit these)` node** in the workflow editor:
   - `GITHUB_OWNER` / `GITHUB_REPO` — the repo to summarize
   - `SUMMARY_EMAIL` — where the digest goes
   - `LANGUAGE` — `EN` or `FR` (the prompt switches language automatically)
   - `CLAUDE_BASE_URL` — `https://api.anthropic.com` for the official API, or your proxy/gateway URL for Anthropic-compatible third-party providers
   - `CLAUDE_MODEL` — defaults to `claude-sonnet-4-20250514`
   - `GITHUB_TOKEN` — a GitHub Personal Access Token with `repo` scope (create one at https://github.com/settings/tokens)
   - `CLAUDE_API_KEY` — your Anthropic key, or a third-party Anthropic-compatible API key

4. **Add SMTP credentials** to the `Send Email (SMTP)` node (Gmail App Password, QQ Mail authorization code, 163 SMTP password — anything that speaks SMTP).

5. **Activate the workflow** with the toggle in the top-right of the editor. It will fire automatically every Friday at 5pm, or click **Execute Workflow** to run it now.

## What It Does

| Step | Node | What |
|------|------|------|
| 1 | Schedule Trigger | Fires every Friday at 17:00 (cron `0 17 * * 5`) |
| 2 | Config | Holds repo/email/language/API settings |
| 3 | Calc Date Range | Computes a 7-day window |
| 4 | 3× HTTP Request | Fetches commits, merged PRs, closed issues from GitHub |
| 5 | Merge | Combines the three streams |
| 6 | Build Claude Prompt | Aggregates raw data into a single prompt, injects EN/FR language directive |
| 7 | Call Claude API | Calls `POST /v1/messages` (works with the official Anthropic API and any Anthropic-compatible third-party gateway) |
| 8 | Format Email | Adds bilingual subject + footer with weekly stats |
| 9 | Send Email | SMTP delivery |

## Language Switch (EN / FR)

Change `LANGUAGE` to `FR` in the Config node. The prompt then instructs Claude to write the entire summary in French, and the email subject/footer also switch language.

## Anthropic-Compatible Proxies

The Claude call uses a raw HTTP Request node, so it works with any provider that exposes an Anthropic-style `/v1/messages` endpoint — official `api.anthropic.com`, OpenRouter, third-party gateways, etc. Just point `CLAUDE_BASE_URL` at the provider.

## Files

| File | Purpose |
|------|---------|
| `weekly-dev-summary.json` | Importable n8n workflow |
| `README.md` | This file |
| `examples/sample-summary.md` | Sample output the workflow produces |
| `examples/screenshot-execution.png` | Real n8n execution screenshot |
