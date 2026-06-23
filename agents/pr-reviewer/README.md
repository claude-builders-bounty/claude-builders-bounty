# PR reviewer agent

This is a small CLI-style reviewer for the PR review bounty. It accepts a public GitHub PR URL, fetches the `.diff`, and prints a structured Markdown review comment.

## Usage

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

Optional local diff mode:

```bash
python agents/pr-reviewer/claude_review.py --diff-file path/to/change.diff
```

Optional output file:

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output format

The generated comment contains:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## Review approach

The reviewer uses the diff itself rather than repository secrets or private API access. It checks changed files, diff size, test coverage signals, docs changes, database/schema paths, dependency files, and auth/security-sensitive paths.
