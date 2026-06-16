.PHONY: test ci-validate

test:
	bash tests/run-ci-checks.sh

ci-validate: test
