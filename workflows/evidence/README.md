# n8n Smoke Execution Evidence

This directory contains local real n8n smoke execution evidence for the weekly dev summary workflow.

## Evidence Files

- `n8n-executions-proof.png` - n8n executions list showing workflow `Weekly GitHub Dev Summary with Claude - Local Execute Proof` succeeded with execution ID 2 in 1.688s.
- `n8n-execution-detail-proof.png` - n8n execution detail page showing `Jun 13 00:31:16` and `Succeeded in 1.688s | ID#2`.
- `webhook-delivery-proof.png` - local webhook delivery page showing the final summary payload was received.
- `webhook-deliveries.json` - JSON delivery evidence. The last delivery metadata contains `repo=claude-builders-bounty/claude-builders-bounty`, `language=EN`, `commits=1`, `closedIssues=1`, and `mergedPrs=1`.
- `n8n-execute-proof-output.json` - n8n CLI raw execution output from the local smoke run.
- `n8n-weekly-dev-summary-execute-proof.json` - local execution workflow copy used for CLI smoke execution.

## Boundary

This is local real n8n 1.97.1 smoke execution evidence with webhook delivery. It is not evidence of a production Anthropic API call.

The submitted workflow in `../n8n-weekly-dev-summary.json` uses a weekly Schedule Trigger. The n8n CLI cannot directly execute that trigger path, so the smoke proof copy replaces only the trigger with an Execute Workflow Trigger. The downstream chain remains the same shape: GitHub activity fetch, Claude Messages request, formatting, and webhook delivery. During the smoke run, GitHub, Claude, and webhook endpoints were local mock services so the workflow could be exercised without external credentials.
