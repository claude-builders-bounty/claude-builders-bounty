# Verification

Target bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

## Commands

```bash
python3 -m unittest discover -s pr-review-agent/tests
python3 pr-review-agent/claude_review.py --help
./claude-review --help
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/891 --output pr-review-agent/samples/sample-output-1.md
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1027 --output pr-review-agent/samples/sample-output-2.md
git diff --check
```

## Notes

- No paid API is required.
- The agent uses `gh` and deterministic local analysis.
- Sample outputs are generated from real GitHub PRs.
