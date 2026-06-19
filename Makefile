# Root Makefile for claude-builders-bounty template validation (bounty #2).
#
# Targets:
#   env-check         — verify node, bash, and git are on PATH (scripts/env-check.mjs)
#   test              — run full template CI suite (env-check + scripts/run-ci-checks.sh)
#   ci-validate       — alias for `test`; used by fleet delivery and GitHub Actions via npm test
#   test-peer-review  — run peer-review acceptance suite only (npm run test:peer-review)
#   test-delivery     — run delivery verification gates only (npm run test:delivery)

.PHONY: test ci-validate env-check test-peer-review test-delivery

# Toolchain probe; fails fast before heavier scaffold/smoke steps.
env-check:
	node scripts/env-check.mjs

# Full validation: structural checks, greenfield smoke test, delivery + peer-review suites.
test: env-check
	bash scripts/run-ci-checks.sh

# CI alias — identical to test so `make ci-validate` matches npm run test:ci wiring.
ci-validate: test

# Peer-review acceptance only — 151+ asserts for bounty #2 / PR #2529 criteria.
test-peer-review:
	npm run test:peer-review

# Delivery gates only — no_committed_diff and peer_review_not_passed without full CI.
test-delivery:
	npm run test:delivery
