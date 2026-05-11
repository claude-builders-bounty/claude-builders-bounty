# PR Review Agent

A Claude Code agent that fetches any GitHub PR, analyzes the diff, and returns a structured code review.

## Quick Start

### CLI

```bash
git clone <this-repo> && cd agents/pr-review
chmod +x claude-review.sh

# Review any PR
./claude-review.sh --pr https://github.com/owner/repo/pull/123

# Or with just the number (requires GITHUB_REPOSITORY env)
GITHUB_REPOSITORY=owner/repo ./claude-review.sh --pr 123
```

**Requirements:** GitHub CLI (`gh`) authenticated, `jq`

### As a Claude Code Agent

1. Copy the `agents/pr-review` folder to your project
2. Tell Claude Code: `claude-review --pr https://github.com/owner/repo/pull/123`
3. Claude Code fetches the full diff and produces a structured review

### As a GitHub Action

Copy `.github/workflows/pr-review.yml` to your project. Any PR comment containing `/review` triggers an automated review comment.

## Output Structure

```
## Review: owner/repo#123

**Title:** PR title
**Author:** @author  **State:** open
**Branch:** `feature-branch` → `main`
**Stats:** +150/-30 across 5 files

### PR Description
(PR body text)

### Diff (256 lines)
(diff content)

### Analysis Checklist
- `src/file.ts` (modified, +50/-10)

### Summary
(2–3 sentence summary of changes)

### Identified Risks
- Risk description with file reference

### Improvement Suggestions
- Suggestion with rationale

### Confidence Score
High / Medium / Low
```

## Examples

See `examples/` for sample outputs:
- [Review of claude-builders-bounty#861](./examples/review-pr861.md) — Changelog skill (4 files, +232 lines)
- [Review of claude-builders-bounty#862](./examples/review-pr862.md) — Destructive command blocker (2 files, +193 lines)
