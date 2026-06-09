.PHONY: test ci-validate

test:
	bash templates/nextjs-sqlite-saas/tests/run-ci-checks.sh

ci-validate: test
