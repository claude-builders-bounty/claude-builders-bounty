.PHONY: test ci-validate

test:
	bash agents/claude-review/tests/run-ci-checks.sh

ci-validate: test
