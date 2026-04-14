# Contributing to claude-builders-bounty

Thank you for your interest in contributing! This PR implements 5 bounties in a single, well-organized submission.

## What's Included

| Bounty | Issue | Amount | Implementation |
|--------|-------|--------|----------------|
| Hook: Pre-tool-use blocker | #3 | $100 | `hooks/hook.py` + tests |
| CHANGELOG generator | #1 | $50 | `changelog/` + SKILL.md |
| PR Review Agent | #4 | $150 | `review-agent/` CLI tool |
| n8n workflow | #5 | $200 | `n8n-workflow/` JSON export |
| CLAUDE.md template | #2 | $75 | `template/` |

**Total: $575**

## Quality Assurance

- ✅ All Python files have automated tests
- ✅ All shell scripts tested in CI
- ✅ GitHub Actions workflow for continuous testing
- ✅ Comprehensive READMEs with ≤5 step installation
- ✅ No external dependencies (pure stdlib Python)
- ✅ SKILL.md integration for Claude Code

## Running Tests

```bash
# Test hook patterns
python3 tests/test_hook.py

# Test changelog generator
bash tests/test_changelog.sh

# Full CI
act -j test-hook  # requires act CLI
```
