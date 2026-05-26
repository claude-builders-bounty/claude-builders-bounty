# PR Reviewer Agent

Structured PR review helper for Claude Code bounty issue #4.

It accepts a GitHub PR URL or a local diff, analyzes the changed files, and prints a structured Markdown review comment with:

- Summary
- Risk assessment
- Suggested changes
- Confidence score

## Usage

Review a public GitHub PR:

```bash
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

Review a local diff:

```bash
git diff main...HEAD | python3 agents/pr-reviewer/claude_review.py --stdin
```

Write output to a file:

```bash
python3 agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## What It Checks

- Number of files and hunks changed
- Added and removed line counts
- Test files touched or missing
- Migration/schema files touched
- Lockfile changes
- Secret-like strings
- Destructive command patterns
- Risk keywords such as auth, billing, payments, delete, truncate, token, and private key

The script is intentionally deterministic so it can be used from Claude Code, CI, or a GitHub Action before a human posts the final comment.

## Example Claude Code Prompt

```text
Use agents/pr-reviewer/claude_review.py to review this PR. Then refine the Markdown with any repository-specific context you find in README, tests, and changed files.
```
