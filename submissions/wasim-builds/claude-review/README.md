# Claude PR Review

Structured PR review agent for Claude Code builders bounty #4.

CLI + GitHub Action that takes a GitHub PR URL, analyzes the diff, and posts a structured Markdown review comment.

## Usage

### CLI

```bash
chmod +x claude-review
./claude-review --pr https://github.com/owner/repo/pull/123
./claude-review --pr https://github.com/owner/repo/pull/123 --out review.md
./claude-review --diff path/to.diff
```

### GitHub Action

Comment `/claude-review` on any PR to trigger the workflow, or dispatch manually with a PR URL.

## Output

```markdown
## Claude Code Review

> **Confidence:** High

### Summary
This PR touches 3 file(s), 120 additions and 45 deletions.

### Identified Risks
- None detected

### Improvement Suggestions
- Pure additive PR — verify tests and docs are included.
```

## Requirements

- Python 3.10+
- `gh` CLI authenticated with repo access
- `GITHUB_TOKEN` for GitHub Action usage
