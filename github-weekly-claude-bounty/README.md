# GitHub Weekly Summary → Claude → Slack/Discord

An importable n8n workflow for the `$200` workflow bounty described in [issue #484](https://github.com/zhangjiayang6835-cyber/bounty-plaza/issues/484).

## Setup

1. Import `github-weekly-summary.json` into n8n.
2. Set the workflow variables in the `Config` node: owner, repository, GitHub token, Anthropic key, destination webhook, and `en` or `fr` language.
3. Set the schedule in `Weekly trigger` (default: Friday at 17:00).
4. Activate the workflow and run it once manually with test data.
5. Confirm the summary arrives in the configured Slack/Discord webhook.

The workflow fetches commits, closed issues, and merged pull requests from the previous seven days, asks Claude for a concise narrative summary, then posts the result to a webhook. Credentials are kept in n8n credentials rather than embedded in the workflow.

## Acceptance checklist

- [x] Exportable JSON workflow
- [x] Weekly cron trigger
- [x] GitHub API collection: commits, closed issues, merged PRs
- [x] Claude API narrative generation
- [x] Slack/Discord-compatible webhook delivery
- [x] Configurable repository, destination, and language
- [ ] Real n8n execution screenshot — must be captured by the claimant after importing with their own credentials

See [`SUBMISSION_READY.md`](SUBMISSION_READY.md) for the exact claim, screenshot, and PR checklist.

Run `python3 verify_workflow.py` for the offline structural checks. These checks do not replace the required real n8n execution screenshot.

## Notes

The workflow intentionally does not auto-claim the bounty, create accounts, or use credentials. Submission and payment require the contributor's GitHub/Opire identity and acceptance by the bounty owner.
