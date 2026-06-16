.PHONY: test ci-validate test-peer-review

test:
	bash tests/run-ci-checks.sh

test-peer-review:
	npm run test:peer-review

ci-validate: test
