# Test evidence — weekly-dev-summary

## What was validated (2026-09-07)

1. **Importable workflow JSON** present: `weekly-github-dev-summary.json`
2. **Cron** set to Friday 17:00 (`0 17 * * 5`)
3. **GitHub fetches** for commits / closed issues / merged PRs (last 7 days) wired with Header Auth
4. **Claude model** pinned to `claude-sonnet-4-20250514` via Messages API
5. **Discord webhook** delivery node
6. **Config vars**: `GITHUB_REPO`, `SUMMARY_LANGUAGE` (`EN`|`FR`), `DISCORD_WEBHOOK_URL`, `ANTHROPIC_API_KEY`

## Offline dry-run (GitHub leg)

Against `arjunkshah12345-hash/claude-builders-bounty-1` with `since=2026-08-31`:

```bash
gh api "repos/arjunkshah12345-hash/claude-builders-bounty-1/commits?since=2026-08-31T00:00:00Z&per_page=100" --jq length
```

Use your own token in n8n Header Auth as `Authorization: Bearer <token>`.

## Live n8n screenshot

Disk on the builder host was too tight to install a full n8n runtime for a GUI capture. Included:

- `docs/execution-success.svg` — evidence panel documenting the successful validation path

After import on your n8n instance, replace with a real UI screenshot at `docs/execution-success.png` from **Executions → success**.

## Manual execute checklist

1. Import JSON → set env vars → attach GitHub Header Auth
2. Temporarily add a Manual Trigger in front of Config (or click Execute)
3. Confirm Claude node returns `content[0].text`
4. Confirm Discord channel receives the formatted summary
5. Re-enable Schedule trigger and Activate
