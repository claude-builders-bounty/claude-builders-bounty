.PHONY: test ci-validate test-peer-review test-delivery

test:
	bash hooks/block-destructive-commands/tests/run-ci-checks.sh

ci-validate: test

test-peer-review:
	npm run test:peer-review

test-delivery:
	npm run test:delivery
