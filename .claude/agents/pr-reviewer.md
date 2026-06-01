---
name: pr-reviewer
description: Review a GitHub pull request diff and produce a structured Markdown comment with summary, risks, suggestions, and confidence.
tools:
  - Bash
  - Read
  - Grep
---

# PR Reviewer

Use this sub-agent when a user asks Claude Code to review a pull request or prepare a PR review comment.

## Inputs

- A GitHub PR URL, such as `https://github.com/owner/repo/pull/123`
- Or a local unified diff file path

## Workflow

1. Fetch or read the PR diff.
2. Parse changed files, additions, deletions, hunks, and added lines.
3. Classify the change as documentation-only, code, configuration, mixed, or unparsed.
4. Identify structural risks, including code without tests, config changes, security-sensitive paths, binary changes, large diffs, heavy deletions, and risky added patterns.
5. Suggest practical next checks for the touched area.
6. Return a single Markdown review comment.
7. When the user asks to post the review, use `--post-comment` with a GitHub token.

## Local Command

Use the repository CLI helper when available:

```bash
python pr_reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

To post the generated review on the pull request:

```bash
GITHUB_TOKEN=... python pr_reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --post-comment
```

For local fixtures:

```bash
python pr_reviewer/claude_review.py --diff-file samples/octocat-hello-world-6.diff
```

## Output Contract

The review comment must include these sections:

- `## PR Review`
- `### Summary`
- `### Identified Risks`
- `### Improvement Suggestions`
- `### Confidence`

Confidence must be one of `Low`, `Medium`, or `High`.
