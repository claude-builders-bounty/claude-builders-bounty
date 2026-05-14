# PR Review Agent

A standalone PR review tool that fetches a PR diff and produces a structured Markdown code review.

## CLI Usage

```bash
# Review a specific PR
python3 claude_review.py --pr https://github.com/owner/repo/pull/123

# Review from diff input
git diff | python3 claude_review.py --diff

# JSON output for programmatic use
python3 claude_review.py --pr owner/repo#123 --json
```

## GitHub Action

Copy `pr-review.yml` to `.github/workflows/` to auto-review all PRs.

## Output Format

- **Summary** of changes (files, lines, critical count)
- **Confidence** score (Low/Medium/High based on change size)
- **Risks** identified (security, data loss)
- **Findings** with severity (critical/warning/info), category, and suggestions
- **Improvement** suggestions (TODOs, optimization opportunities)

## Detection Patterns

| Category | Patterns Detected |
|----------|-------------------|
| Security | Hardcoded secrets, eval/exec, SQL injection |
| Error Handling | Bare except, silenced exceptions |
| Maintainability | TODO/FIXME markers, complex patterns |
