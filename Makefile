# Makefile targets for issue #521 README link validation (PR #2532).
# All targets delegate to npm scripts or tests/run-ci-checks.sh.
.PHONY: test ci-validate test-peer-review test-readme-links test-delivery

# Full CI suite: readme links, peer-review acceptance, delivery verification.
test:
	bash tests/run-ci-checks.sh

# Alias for `make test` — used by contributors and fleet delivery checks.
ci-validate: test

# Individual suites (match package.json scripts for local debugging).
test-peer-review:
	npm run test:peer-review

test-readme-links:
	npm run test:readme-links

test-delivery:
	npm run test:delivery
