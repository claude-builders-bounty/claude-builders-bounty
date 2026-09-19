## Summary

Adds an importable n8n workflow that creates a weekly Claude narrative from a GitHub repository's activity and delivers it to Slack or Discord.

## Included

- Weekly cron trigger.
- GitHub commits, closed issues, and merged pull requests from the previous seven days.
- Claude `claude-sonnet-4-20250514` generation.
- Configurable repository, language, and destination webhook.
- Setup instructions in five steps or fewer.
- Offline structural verifier: `python3 verify_workflow.py`.

## Validation

The offline verifier passes. A real n8n execution screenshot must be attached after importing the workflow with the claimant's own GitHub, Anthropic, and Slack/Discord credentials.

## Security

No live credentials are included. Configure secrets in n8n credentials or environment variables before activation.
