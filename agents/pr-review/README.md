# PR Review Agent (claude-review)

Analyzes PR diffs and returns structured Markdown review comments.

## Usage

```bash
bash claude-review.sh --pr https://github.com/owner/repo/pull/123
# OR
bash claude-review.sh --diff path/to/diff.patch
```

## Output

Structured review with:
- Summary of changes
- Identified risks
- Improvement suggestions
- Verdict
