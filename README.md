# Claude Review

CLI tool that analyzes a GitHub pull request diff and produces a structured Markdown review.

## Usage

```bash
./claude-review.py --pr https://github.com/owner/repo/pull/123
```

The report contains:
- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score (Low / Medium / High)
- Changed files

## Requirements

- Python 3.9+
- Internet access to the GitHub API

## Examples

Two real GitHub PR review outputs are included:
- `sample-review-1.md`
- `sample-review-2.md`
