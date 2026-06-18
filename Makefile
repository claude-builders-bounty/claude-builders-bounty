# Root Makefile for claude-builders-bounty template validation (bounty #2).
#
# Targets:
#   env-check    — verify node, bash, and git are on PATH (scripts/env-check.mjs)
#   test         — run full template CI suite (env-check + scripts/run-ci-checks.sh)
#   ci-validate  — alias for `test`; used by fleet delivery and GitHub Actions via npm test

.PHONY: test ci-validate env-check test-peer-review test-delivery

# Toolchain probe; fails fast before heavier scaffold/smoke steps.
env-check:
	node scripts/env-check.mjs

# Full validation: structural checks, greenfield smoke test, delivery + peer-review suites.
test: env-check
	bash scripts/run-ci-checks.sh

# CI alias — identical to test so `make ci-validate` matches npm run test:ci wiring.
ci-validate: test

# Isolated fleet entry points for hands-on delivery without the full CI runner.
test-peer-review:
	npm run test:peer-review

test-delivery:
	npm run test:delivery
