# PR reviewer regression verification — 3 October 2026

Changed behavior: unified-diff file headers are excluded from change counts; review sections must be ordered and non-empty; risk/suggestion lists and an exact confidence value are required. The prompt is self-contained, Claude launch/time-out failures fall back, and diff-fetch errors return a clear nonzero result.

Focused tests: 12 passed. Python compilation and git diff --check passed.

Two current real GitHub PR diffs were fetched via gh and reviewed with --fallback-only; both commands exited 0 and passed the Markdown contract:
- https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4666 — issue-4-pr-review-agent/samples/verified-fallback-pr4666.md
- https://github.com/cc-mug-up-lab/aie-b3-upstream/pull/6 — issue-4-pr-review-agent/samples/verified-fallback-calculator-pr6.md

This run does not call a live Anthropic model. The previous official-Claude-binary/local-endpoint receipt remains a historical integration receipt for the earlier revision, not a fresh hosted-model execution.
