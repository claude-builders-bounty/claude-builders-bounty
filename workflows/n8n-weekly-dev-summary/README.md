# n8n Weekly Dev Summary Workflow

This submission implements bounty [#5](../../../issues/5): an n8n workflow that gathers the last seven days of GitHub commits, closed issues, and merged pull requests, asks Claude to summarize them, and posts the digest to Slack.

## Files

- `workflow.json` — importable n8n workflow.
- `sample-output.md` — example weekly digest generated from representative commit bullets.
- `validate_workflow.py` — lightweight structural validator for the workflow JSON.

## Required Environment

Set these values in the n8n environment before enabling the workflow:

```text
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_OWNER=OWNER
GITHUB_REPO=REPO
DIGEST_LANGUAGE=EN
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#engineering
```

The GitHub HTTP nodes use n8n's `githubApi` credential type. The Claude API key, Slack webhook, destination channel, target repository, and output language are environment variables so secrets do not live in the workflow export.

## Import

1. Open n8n.
2. Choose **Import from File** and select `workflow.json`.
3. Configure the `githubApi` credential on all three GitHub fetch nodes.
4. Add the environment variables above.
5. Run the workflow manually once, then enable it.

## Workflow Steps

1. **Weekly Friday Schedule** runs every Friday at 17:00.
2. **Fetch GitHub Commits**, **Fetch Closed Issues**, and **Fetch Merged PRs** gather weekly repo activity.
3. **Build Weekly Activity** normalizes the three API responses into a single Markdown prompt.
4. **Summarize with Claude** calls `claude-sonnet-4-20250514`.
5. **Extract Claude Text** and **Post to Slack** deliver the narrative digest to the configured channel.

## Validate

```bash
python workflows/n8n-weekly-dev-summary/validate_workflow.py
```

Expected:

```text
workflow.json OK: 8 nodes, 7 connections
```

## Screenshot Requirement

The bounty asks for a screenshot of the workflow running in a real n8n instance. I did not commit a fabricated screenshot; the included validator confirms the importable workflow structure and required variables, while a live screenshot should be captured from a credentialed n8n workspace.
