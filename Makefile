.PHONY: test ci-validate

test:
	cd workflows/n8n-weekly-dev-summary && npm run test:ci

ci-validate: test
