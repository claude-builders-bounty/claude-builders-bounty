# Weekly GitHub Dev Summary — n8n + Claude

1. Import `workflow.json` into n8n.
2. Set `GITHUB_TOKEN` (repo read access) and `GITHUB_REPO=owner/repo` in the n8n environment.
3. Set `SUMMARY_LANGUAGE=EN` (or `FR`), `ANTHROPIC_API_KEY`, `SLACK_WEBHOOK_URL`, and optional `SLACK_CHANNEL`.
4. Run once manually and verify the Slack message; the schedule is Friday at 17:00.
5. Activate the workflow.

The workflow fetches commits, closed issues, and merged PRs from the last seven days in a deterministic sequential chain, asks `claude-sonnet-4-20250514` for a factual narrative summary, then posts it to the configured Slack destination. `ANTHROPIC_API_URL` is optional and defaults to `https://api.anthropic.com/v1/messages`.

## Verification

`validate_workflow.py` checks the production export, exact Friday 17:00 schedule, GitHub/Claude/Slack stages, requested Claude model, configurable repo/language/destination values, and the complete `Claude Summary → Extract Summary → Send to Slack` path. It also validates the supplementary credential-free verification receipt.

### Production-like real n8n run

The production workflow chain was imported and executed on **n8n 1.82.3 in Docker on 2026-10-03**. The run completed through the final `Send to Slack` node with CLI exit code 0 and a successful UI execution. See [`evidence/n8n-success.png`](evidence/n8n-success.png) and [`evidence/verification.md`](evidence/verification.md).

That run used the **live public GitHub API**. The verification host did not have Anthropic or Slack credentials, so only those two network transports were replaced with deterministic local endpoints. The Anthropic verifier observed the exact `claude-sonnet-4-20250514` request and the Slack verifier received the normalized summary text. Production defaults remain the real Anthropic endpoint and the configured Slack webhook.

Real-instance testing also exposed and fixed three runtime issues that structural validation alone did not catch: the Set-node export schema, zero-activity GitHub responses stopping the chain, and raw POST response streams preventing Claude/Slack JSON parsing.

### Supplementary credential-free n8n run

`verification_workflow.json` remains a separate credential-free fixture for reviewers who want a no-secret/no-spend import check. It was imported and executed end-to-end in **n8n 2.41.6** on 2026-10-03. All four nodes completed successfully and the final node emitted `status: PASS` plus `delivery: captured-not-sent`. See [`verification-n8n-execution.svg`](verification-n8n-execution.svg) and [`verification_receipt.json`](verification_receipt.json).

Evidence boundary: neither verification run claims a live Anthropic API charge or a real Slack workspace delivery. A production run still requires valid `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, and `SLACK_WEBHOOK_URL` values.

Fresh validation: `python validate_workflow.py` → **workflow contract: PASS** and **verification contract: PASS**.
