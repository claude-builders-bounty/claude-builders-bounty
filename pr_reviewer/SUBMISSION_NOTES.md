# Submission Notes

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

## Summary

This package adds a dependency-free CLI agent that reviews a pull request diff and returns a structured Markdown review comment.

It supports:

- A Claude Code sub-agent definition at `.claude/agents/pr-reviewer.md`
- `claude-review --pr https://github.com/owner/repo/pull/123`
- `.\claude-review.cmd --pr https://github.com/owner/repo/pull/123` on Windows
- `python pr_reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123`
- `python pr_reviewer/claude_review.py --diff-file samples/octocat-hello-world-6.diff`
- `--output review.md` for saving the review comment
- `--post-comment` for posting the review directly to the pull request
- `.github/workflows/claude-pr-review.yml` for automated review comments on PR events

## Verification

```powershell
python -m py_compile .\pr_reviewer\claude_review.py .\pr_reviewer\test_claude_review.py
python .\pr_reviewer\test_claude_review.py
```

## Sample Outputs

The included samples were generated from real public GitHub PRs:

- https://github.com/octocat/Hello-World/pull/1
- https://github.com/octocat/Hello-World/pull/6

## Files

- `claude-review`
- `claude-review.cmd`
- `claude-review.ps1`
- `.claude/agents/pr-reviewer.md`
- `.github/workflows/claude-pr-review.yml`
- `pr_reviewer/claude_review.py`
- `pr_reviewer/test_claude_review.py`
- `pr_reviewer/README.md`
- `samples/octocat-hello-world-1.diff`
- `samples/octocat-hello-world-1.md`
- `samples/octocat-hello-world-6.diff`
- `samples/octocat-hello-world-6.md`
