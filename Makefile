.PHONY: test ci-validate test-peer-review test-delivery

test:
	cd workflows/n8n-weekly-dev-summary && npm run test:ci

ci-validate: test

test-peer-review:
	cd workflows/n8n-weekly-dev-summary && npm run test:peer-review

test-delivery:
	cd workflows/n8n-weekly-dev-summary && npm run test:delivery
