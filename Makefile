.PHONY: test ci-validate

test:
	bash hooks/block-destructive-commands/tests/run-ci-checks.sh

ci-validate: test
