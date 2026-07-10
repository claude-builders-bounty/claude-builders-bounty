# Weekly GitHub Dev Summary — n8n + Claude API

Automated workflow that, once a week, pulls your org's merged PRs and open issues,
summarizes them with Claude, and posts the digest (Slack / Discord / Markdown file).

## What's included
- `workflow.json` — importable n8n workflow (n8n → Settings → Import).
- `summary_prompt.md` — the system prompt handed to Claude for the digest.
- `README.md` — setup + credentials.

## Setup
1. In n8n, **Import** `workflow.json`.
2. Add credentials:
   - **GitHub OAuth2** (or a `GITHUB_TOKEN`) on the GitHub nodes.
   - **Anthropic API Key** on the HTTP Request node that calls Claude.
3. Set the Schedule trigger to your preferred cadence (default: Mon 09:00).
4. Edit the `owner`/`repo` values in the GitHub nodes.
5. Point the final node at Slack/Discord/email, or leave it writing a Markdown file.

## How it works
```
Schedule (weekly)
   → GitHub: list merged PRs (last 7d)
   → GitHub: list open issues
   → Aggregate into one prompt
   → Claude (claude-sonnet-4): write the digest
   → Post digest to Slack/Discord/Markdown
```

## Claude prompt (summary_prompt.md)
The workflow sends this system prompt plus the raw JSON of PRs/issues.
Claude returns a concise, scannable weekly report.

## Notes
- Free-tier friendly: ~1 call/week, tiny payload.
- Swap the Claude call for any chat-completions endpoint if preferred.
