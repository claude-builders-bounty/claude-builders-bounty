# n8n Local Validation

Validation was run without printing or committing any API secrets.

## Commands

```sh
node scripts/validate-n8n-workflow.mjs
```

## Result

```text
Validated n8n-weekly-dev-summary.json with 17 nodes and 5 setup steps.
```

## Notes

- The workflow includes a real weekly schedule trigger for Friday at 17:00.
- The production path fetches commits, closed issues, and merged pull requests from the GitHub API.
- The production path calls Anthropic Messages API with `claude-sonnet-4-20250514`.
- The delivery path posts either Slack or Discord webhook payloads.
- `N8N_WEEKLY_DRY_RUN=true` routes to sample activity and a mock Claude summary so the workflow can be checked without exposing credentials in a public PR.
