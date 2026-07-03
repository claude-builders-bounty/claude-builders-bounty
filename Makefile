.PHONY: test ci-validate test-peer-review test-delivery

# Full n8n weekly-dev-summary regression suite (workflow structure, GitHub helpers, delivery, peer-review).
test:
	cd workflows/n8n-weekly-dev-summary && npm run test:ci

# Alias for CI pipelines that expect a ci-validate target.
ci-validate: test

# Isolated peer-review acceptance gate (bounty #5 acceptance criteria).
test-peer-review:
	cd workflows/n8n-weekly-dev-summary && npm run test:peer-review

# Fleet delivery verification gate (branch diff, PROOF, npm test wiring).
test-delivery:
	cd workflows/n8n-weekly-dev-summary && npm run test:delivery
