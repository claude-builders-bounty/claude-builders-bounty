# Public Submission Draft

Do not post, push, open a PR, create accounts, accept terms, or enter payment details until the user explicitly approves that public action.

## Claim Comment

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5

Post this as a standalone issue comment only after approval:

```text
/opire try
```

## Pull Request

Open the PR only after the real evidence gate passes and the user approves public submission.

- Base repository: `claude-builders-bounty/claude-builders-bounty`
- Base branch: `main`
- Head branch: `bounty/issue-5-weekly-dev-summary`
- Title: `Add n8n weekly dev summary workflow`
- Body source: `submissions/aviranchigoda/PR_DESCRIPTION.md`
- Changed-file scope: `submissions/aviranchigoda/`

## Pre-Submission Commands

Run these immediately before public submission:

```bash
node submissions/aviranchigoda/pre-submit-audit.mjs --require-real-evidence
git -c core.fsmonitor=false diff --name-only origin/main...HEAD
```

The strict audit must pass. The changed-file list must contain only paths under `submissions/aviranchigoda/`.

## Evidence To Mention If Asked

- Importable workflow: `submissions/aviranchigoda/weekly-dev-summary.workflow.json`
- Acceptance map: `submissions/aviranchigoda/ACCEPTANCE_MATRIX.md`
- Real evidence runbook: `submissions/aviranchigoda/REAL_EVIDENCE.md`
- Local mock execution evidence: `submissions/aviranchigoda/evidence/mock-execution-result.json`
- Mock Slack failure evidence: `submissions/aviranchigoda/evidence/mock-slack-failure-result.json`
- Mock n8n UI screenshot: `submissions/aviranchigoda/evidence/mock-n8n-execution-ui.png`
- Real endpoint evidence, after approval: `submissions/aviranchigoda/evidence/real-execution-result.json`
- Real n8n screenshot, after approval: `submissions/aviranchigoda/evidence/real-n8n-execution-ui.png`

## Stop Conditions

- Do not submit if `pre-submit-audit.mjs --require-real-evidence` fails.
- Do not include API keys, webhook URLs, cookies, account data, local n8n user folders, or payment details.
- Do not proceed to Lightspeed or Binance work until the bounty payout is awarded and verified.
