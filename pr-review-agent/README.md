# PR Review Agent

Review a GitHub pull request diff and generate a structured Markdown comment.

## Setup

1. Copy `claude_review.py` into any machine with Python 3.10+.
2. Run `python claude_review.py --pr https://github.com/owner/repo/pull/123`.
3. Paste the Markdown output into the pull request review thread.

## Usage

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
python claude_review.py --diff ./pull-request.diff
```

The CLI fetches the PR `.diff` URL, analyzes changed files, detects risk signals, and returns:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

No API key is required. If `--diff` is provided, the tool runs fully offline.

## Sample Outputs

See:

- `samples/fastapi-template-pr-2297.md`
- `samples/gitearn-pr-30.md`
