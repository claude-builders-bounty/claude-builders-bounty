# Review: fix: support required SDK trust anchors

PR: https://github.com/Terminal-3/adk-circle-call-centre-agent-demo/pull/1

## Summary

This pull request, **#1 — fix: support required SDK trust anchors**, changes 11 files (+210/-166).
The visible change surface includes `agent/src/loop.ts`, `agent/src/t3n-client.ts`, `agent/src/tools/payForService.ts`, `dashboard/app/api/ledger/route.ts` and other files.

## Identified risks

- No high-risk pattern was detected by the deterministic checks; this is not a security guarantee.

## Improvement suggestions

- Add or update focused automated tests for the changed behavior, including one failure path.
- Run the repository's formatter, linter, and full test suite before merging.

## Confidence

High

