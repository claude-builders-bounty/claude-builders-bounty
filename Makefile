.PHONY: test ci-validate env-check

env-check:
	node scripts/env-check.mjs

test: env-check
	bash templates/nextjs-sqlite-saas/tests/run-ci-checks.sh

ci-validate: test
