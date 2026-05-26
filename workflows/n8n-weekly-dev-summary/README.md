# n8n Weekly Dev Summary

Automated weekly engineering summary workflow for issue #5.

The workflow:

1. Runs every Monday morning.
2. Pulls recent GitHub commits, issues, and pull requests.
3. Sends the collected activity to Claude.
4. Produces a concise weekly dev summary.
5. Sends the summary to Slack.

## Import

1. Open n8n.
2. Import `weekly-dev-summary.workflow.json`.
3. Configure credentials:
   - GitHub API credential
   - Anthropic API credential
   - Slack credential
4. Set workflow variables:
   - `owner`
   - `repo`
   - `slackChannel`
5. Run manually once, then activate.

## Required n8n Variables

```text
owner=your-org
repo=your-repo
slackChannel=#engineering
```

## Claude Prompt

The prompt asks Claude to produce:

- Executive summary
- Shipped changes
- Open risks
- PRs needing attention
- Suggested next actions

It also asks Claude to avoid inventing facts and to cite the activity items it used.

## Test Instructions

1. Import the workflow into a local n8n instance.
2. Replace credentials with test credentials or mock nodes.
3. Run the workflow manually.
4. Confirm Slack receives a Markdown summary.
5. Confirm the summary contains commits, issues, PRs, risks, and next actions.

## Files

- `weekly-dev-summary.workflow.json`: importable n8n workflow.
- `sample-summary.md`: example final Slack message shape.
