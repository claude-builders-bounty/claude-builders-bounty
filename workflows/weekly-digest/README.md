# Weekly GitHub digest

Import `weekly-digest.json` into n8n to summarize seven days of activity on a public repository with a default branch. The schedule runs each Friday at 17:00 UTC. A manual run uses the seven days immediately preceding execution.

## Setup

1. Import the workflow JSON in your n8n editor. Leave it inactive while configuring it.
2. In **Settings**, set `repo` to `owner/repository`, `language` to `EN` or `FR`, and set the sender and recipient email addresses. Choose a Claude model available to your organization. The export defaults to `claude-sonnet-4-6`. Anthropic retired the original issue's `claude-sonnet-4-20250514` on June 15, 2026. [Model lifecycle](https://platform.claude.com/docs/en/about-claude/model-deprecations)
3. For **Claude narrative**, select an n8n Header Auth credential with the header name `x-api-key`. For **Email digest**, select your SMTP credential. Keep credential values in n8n's credential store. The GitHub requests read public data anonymously and are subject to GitHub's rate limit.
4. When ready to make a billed model call and send a real email, run the manual trigger and inspect the execution. The separate loopback test below exercises the wiring locally.
5. Publish or activate the workflow only when you want scheduled emails. The schedule uses the workflow's UTC timezone.

The workflow follows GitHub pagination and counts commits on the default branch, issues closed during the window, and merged PRs from all branches. It discards PR entries from the issues endpoint and checks each event's own timestamp. The narrative includes full counts and up to 80 titles or commit subjects per category. The three API listings are collected sequentially. Edits made during pagination can change the underlying data. Completeness also depends on GitHub visibility and rate limits. A failed fetch or incomplete Claude reply stops delivery.

## Local execution test

The test uses a real n8n CLI in a temporary profile. A loopback server supplies two pages of GitHub-shaped data and a deterministic Claude-shaped reply. A local SMTP server captures the outgoing message. The test checks the second commit page, excludes a PR from the issue count and filters out an older issue and an unmerged PR. It verifies the narrative received by the SMTP fixture.

n8n 2.49.6 completed this fixture execution on November 25, 2026. [Execution in the n8n editor](fixture-execution.png) · [Test receipt](fixture-receipt.json)

```sh
python3 test_fixture.py --n8n /absolute/path/to/n8n
```

If the n8n entry point is a JavaScript file, pass `--node` and the absolute Node executable as well. Add `--output /path/to/test-results` to save the n8n execution log and a receipt. The test neither uses Anthropic credentials nor sends an external email.
