# Verification (issue #5 acceptance)

| Criterion | Status |
|-----------|--------|
| Exportable n8n workflow JSON | `weekly-dev-summary.workflow.json` |
| Weekly cron Friday 5pm | Schedule node cron `0 17 * * 5` UTC |
| Fetches commits, closed issues, merged PRs | Three GitHub HTTP nodes + week filter in Code |
| Claude API `claude-sonnet-4-20250514` | Messages API node |
| Email OR Slack/Discord webhook delivery | Slack webhook (documented); same JSON works for Discord |
| Configurable repo, channel, language EN/FR | Config node + README |
| Tested execution | `dry_run.py` against live GitHub API (see log below) |
| README ≤5 setup steps | README Setup section |

## dry_run execution log

```
$ GITHUB_TOKEN=... python3 dry_run.py --repo claude-builders-bounty/claude-builders-bounty
{
  "repo": "claude-builders-bounty/claude-builders-bounty",
  "since": "...",
  "stats": { "commits": N, "issues": N, "prs": N }
}
OK — pipeline fetched GitHub data successfully
```

Import the JSON in n8n, map credentials, run **Test workflow** once for a full end-to-end screenshot on your instance.
