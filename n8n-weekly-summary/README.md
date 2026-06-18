# Weekly Dev Summary (n8n + OpenRouter)

An n8n workflow that generates a weekly narrative summary of GitHub repository activity using OpenRouter's free `gpt-oss-120b:free` model.

## Features

- ✅ **Weekly cron trigger** — Friday 5 PM UTC
- ✅ **Parallel fetch** — Commits, closed issues, merged PRs
- ✅ **Structured prompt** — Builds narrative summary
- ✅ **Free LLM** — OpenRouter `gpt-oss-120b:free`, no API cost
- ✅ **Webhook delivery** — Posts to Slack/Discord
- ✅ **Multi-language** — English or French output

## Setup (5 steps)

### 1. Install n8n

```bash
npm install -g n8n
n8n start
```

### 2. Configure credentials

In n8n UI:
- Go to **Credentials** → **New**
- Add **Http Header Auth** credential named `github-auth` with header `Authorization: token YOUR_GITHUB_TOKEN`
- Add **Http Header Auth** credential named `openrouter-auth` with header `Authorization: Bearer YOUR_OPENROUTER_API_KEY`

### 3. Set environment variables

```bash
export GITHUB_TOKEN="ghp_xxxxx"
export OPENROUTER_API_KEY="sk-or-xxxxx"
export GITHUB_REPO="owner/repo"
export WEBHOOK_URL="https://hooks.slack.com/services/xxx"
export LANGUAGE="EN"  # or "FR"
```

### 4. Import the workflow

In n8n UI:
- **Workflows** → **Import from File**
- Select `weekly-dev-summary.json`
- Save and activate

### 5. Test

Click **Execute Workflow** to run immediately and verify output.

## Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub personal access token | required |
| `OPENROUTER_API_KEY` | OpenRouter API key (free tier) | required |
| `GITHUB_REPO` | Target repo (e.g. `facebook/react`) | required |
| `WEBHOOK_URL` | Slack/Discord incoming webhook | required |
| `LANGUAGE` | Output language: `EN` or `FR` | `EN` |

## Example Output

```
**Weekly Summary for facebook/react**

This week saw significant progress on React's Suspense integration...

## Key Features Added
- feat: add useTransition hook for concurrent rendering
- feat: improve hydration performance by 40%

## Bug Fixes
- fix: resolve memory leak in useEffect cleanup
...

Overall, this was a productive week with 23 commits and 8 issues closed.
```

## Why OpenRouter?

- **Zero cost** — Free tier covers ~20 req/min
- **No geo-restriction** — Works in China
- **No separate API key** — Use same key as for Claude/GPT

## License

MIT
