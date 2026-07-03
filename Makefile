# Root Makefile for claude-builders-bounty template validation (bounty #2).
#
# Targets:
#   env-check         — verify node, bash, and git are on PATH (scripts/env-check.mjs)
#   test              — full CI: security, structural, reference Vitest, delivery + peer-review
#   test-peer-review  — bounty #2 acceptance criteria only (185+ asserts; npm run test:peer-review)
#   test-delivery     — fleet delivery gates only (no_committed_diff + peer_review_not_passed;
#                       also E2E-runs npm test and test:peer-review; npm run test:delivery)

.PHONY: test env-check test-peer-review test-delivery

# Toolchain probe; fails fast before heavier scaffold/smoke steps.
env-check:
	node scripts/env-check.mjs

# Full validation: structural checks, greenfield smoke test, delivery + peer-review suites.
test: env-check
	bash scripts/run-ci-checks.sh

# Peer-review acceptance only — 185+ asserts for bounty #2 / PR #2529 criteria.
test-peer-review:
	npm run test:peer-review

# Fleet delivery gates only — no_committed_diff + peer_review_not_passed; E2E-runs npm test + test:peer-review.
test-delivery:
	npm run test:delivery
