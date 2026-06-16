.PHONY: test ci-validate test-peer-review test-readme-links

test:
	bash tests/run-ci-checks.sh

test-peer-review:
	npm run test:peer-review

test-readme-links:
	npm run test:readme-links

ci-validate: test
