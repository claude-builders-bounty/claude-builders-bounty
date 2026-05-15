## Proposed Changes

Adds a Claude Code PR review agent package:

- `scripts/claude-review`: zero-dependency Python CLI supporting `claude-review --pr <url>`
- `agents/pr-reviewer-agent.md`: Claude Code agent instructions and output contract
- `CLAUDE_REVIEW.md`: setup, CLI usage, and GitHub Action example
- `samples/`: structured Markdown outputs from two real GitHub PRs
- `tests/test_claude_review.py`: parser, diff analysis, risk detection, and output-format tests

/claim #4

## Proof

```bash
python3 -m unittest tests/test_claude_review.py
....
----------------------------------------------------------------------
Ran 4 tests in 0.001s

OK
```

Sample outputs were generated from:

- https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1392
- https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1394

## Checklist

- [x] Works via CLI: `scripts/claude-review --pr https://github.com/owner/repo/pull/123`
- [x] Includes GitHub Action usage YAML in docs
- [x] Structured Markdown output includes summary, risks, suggestions, and confidence
- [x] Tested on two real GitHub PRs with outputs included
- [x] README-style setup and usage instructions included
