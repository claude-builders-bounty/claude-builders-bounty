.PHONY: test ci-validate test-peer-review test-readme-links test-delivery test-issue-2853 verify-issue-2853

test:
	bash tests/run-ci-checks.sh

test-peer-review:
	npm run test:peer-review

test-readme-links:
	npm run test:readme-links

test-delivery:
	npm run test:delivery

test-issue-2853:
	npm run test:issue-2853

verify-issue-2853:
	bash tests/verify-issue-2853.sh

ci-validate: test
