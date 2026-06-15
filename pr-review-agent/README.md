# claude-review — PR Review Agent

Analyze any GitHub PR diff and produce a structured Markdown review comment.

## Setup (2 steps)

```bash
# 1. Ensure gh CLI is authenticated
gh auth status

# 2. Run the agent
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Output

```markdown
# PR Review: https://github.com/owner/repo/pull/123

**Confidence:** High

## Summary
This PR changes 2 file(s) with 23 additions and 1 deletions.

**Files:** 2 | **+23** / **-1**

## Risks Identified
- No significant risks identified.

## Suggestions
- No test files detected. Consider adding tests.
```

## Sample Outputs

### Test 1: git-context PR #58
```
Confidence: High | 2 files | +23/-1
```

### Test 2: claude-builders-bounty PR #2800
```
Confidence: High | 5 files | +200/-0
Risk: subprocess usage detected in changelog.py
```

## Features

- **Diff-aware:** Parses `git diff` output to count per-file changes
- **Risk detection:** Flags large diffs, SQL migrations, secrets files, security-sensitive calls
- **Confidence scoring:** Low/Medium/High based on PR size and change complexity
- **Structured Markdown:** Ready to paste into GitHub PR review comments
- **Zero dependencies:** Uses only Python stdlib + `gh` CLI
