# Template validation tests

CI and fleet delivery scripts for the Next.js 15 + SQLite SaaS `CLAUDE.md` template.

## Contents

| File / script | Purpose |
|---------------|---------|
| `check-secret-tokens.mjs` | Scans workflows and sources for hardcoded secrets; validates `SESSION_SECRET` length |
| `check-sql-parameterization.mjs` | Audits query modules for parameterized SQL (no string interpolation) |
| `check-claude-md.mjs` | Validates `CLAUDE.md` sections, stack pins, and code examples |
| `validate-template.mjs` (parent dir) | Structural validator for opinionated reasons and smoke-test steps |
| `smoke-greenfield.sh` | Scaffolds Next.js 15 and copies `CLAUDE.md` into a temp project; retries under `.cache/smoke-workdirs/` when `/tmp` is non-writable |
| `delivery-verification.test.mjs` | Fleet `no_committed_diff` and `peer_review_not_passed` gates |
| `peer-review-acceptance.test.mjs` | Bounty #2 acceptance criteria for PR #2529 |
| `ci-step-*.sh` | Focused CI stages (security, structural, reference, delivery, peer-review) |
| `run-ci-checks.sh` | Orchestrates all stages; invoked by repo-root `npm test` |
| `reference/scripts/run-tests.sh` | Reference Vitest runner; sets `TMPDIR=node_modules/.tmp` to avoid cache ENOENT flakes |

## Run locally

```bash
# Full CI (same as repo-root npm test / make test)
bash templates/nextjs-sqlite-saas/tests/run-ci-checks.sh

# Fleet delivery gates only (E2E-runs npm test + test:peer-review; ~15s)
npm run test:delivery
# or: make test-delivery

# Peer-review acceptance only (~1s)
npm run test:peer-review
# or: make test-peer-review
```
