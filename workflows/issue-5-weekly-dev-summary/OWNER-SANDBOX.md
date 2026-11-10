# Owner-managed live acceptance for issue #5

Status: **not executed here**. This checklist is not successful-execution evidence.
The owner needs an isolated n8n instance, an owner-funded Anthropic test account,
and a disposable Discord channel/webhook. No keys or webhook URLs should be sent
to the contributor, committed, or posted in GitHub comments. No production data,
payment-account changes, or new paid account are required from the contributor.

1. Import the JSON from the exact PR head under review into a disposable owner
   sandbox. Record the Git commit, JSON SHA-256 and n8n version. Keep the workflow
   inactive so there are no repeat scheduled charges. Use a public repository
   with recent commits, closed issues and merged PRs; no GitHub token is needed.
2. Configure the variables in the five-step README inside that sandbox only.
   Because this export uses environment-variable expressions, permit environment
   access only in this isolated instance; do not weaken a shared/production n8n
   instance. The owner approves the cost of one model request before starting.
3. Manually execute once. Confirm all nine nodes succeed, the GitHub activity
   matches the seven-day window, Claude returns narrative text, and the actual
   Discord channel receives the summary. Record execution ID and UTC timestamps.
   A fixture, import success, resolver test or mocked Claude response is not this
   acceptance test. Check FR in a second owner-approved run if desired.
4. Capture the successful n8n execution and the received Discord message. Review
   every image/export locally for keys, Authorization headers, webhook URL/tokens,
   private data and account identifiers before sharing. Do not upload raw run
   exports. The optional checker below is for owner-local inspection only.
5. Post sanitized screenshots plus the commit/hash, n8n version, execution ID,
   times and an explicit owner attestation that real Claude and Discord were used.
   Disable the workflow and revoke the disposable webhook after evidence capture.
   The maintainer decides acceptance and payment; the checker cannot do that.

## Optional owner-local execution structure check

For an n8n execution JSON object containing `data.workflowData` and
`data.resultData.runData` (not a workflow-only export), run:

```bash
python workflows/issue-5-weekly-dev-summary/check_execution_evidence.py /private/path/execution.json
```

The file stays local. The checker prints no node payloads and sends no requests.
It rejects failed/incomplete runs, changed executable nodes/connections, missing
model text and absent/oversized prepared Discord messages. Unsupported export
shapes fail closed. It checks structure, **not authenticity**, actual HTTP
delivery, screenshots, spend approval, or secret redaction. The owner must still
verify Discord receipt and attest the provenance. Its synthetic unit fixtures
are explicitly not live evidence.
