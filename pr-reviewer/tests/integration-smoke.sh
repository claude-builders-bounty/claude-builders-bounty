#!/usr/bin/env bash
set -euo pipefail
node src/cli.js --pr https://github.com/openai/openai-python/pull/2345 >/tmp/claude-review-smoke.md
grep -q '## Summary' /tmp/claude-review-smoke.md
grep -q '## Risks' /tmp/claude-review-smoke.md
grep -q '## Improvement Suggestions' /tmp/claude-review-smoke.md
grep -q '## Confidence' /tmp/claude-review-smoke.md
