# claude-review — Claude Code PR Review Sub-Agent

## Description
A Claude Code sub-agent that reviews GitHub PRs and produces structured Markdown reports. Run as a standalone CLI or as a GitHub Action.

## Usage
```bash
# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123

# Review a local diff
claude-review --diff /tmp/pr.diff --output review.md

# Review and post comment
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

## What it checks
- **Code style**: line length, tabs, trailing whitespace, debug prints
- **Potential bugs**: None assignments, bare excepts, empty blocks, eval usage
- **Security**: hardcoded secrets, SQL injection, XSS, command injection, disabled SSL
- **Performance**: O(n²) loops, inefficient DOM queries, sequential awaits
- **Test coverage**: missing test files for source changes
- **Documentation**: missing README/docs updates for new functions

## Output sections
1. Summary of Changes (2-3 sentences)
2. Identified Risks (per-category lists with severity)
3. Improvement Suggestions
4. Confidence Score (Low/Medium/High)

## Integration
- **Standalone CLI**: `python pr-review-agent/claude-review.py --pr <url>`
- **GitHub Action**: included `.github/workflows/pr-review.yml`
- **Claude Code sub-agent**: reference this CLAUDE.md in your project
