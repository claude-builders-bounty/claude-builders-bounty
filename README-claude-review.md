# Claude Review

`claude_review.py` is a small CLI agent that reviews a GitHub pull request diff and returns a structured Markdown comment.

## Usage

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

The command fetches the public `.diff` for the pull request and prints:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

## Notes

- No package installation is required.
- The PR must be public, or the diff URL must be accessible from the current environment.
- The review is deterministic and based on diff shape, changed paths, and whether tests/docs are present.
- It does not post comments automatically; copy the output into GitHub only after review.

## Validation

Tested on two public pull requests:

```bash
python claude_review.py --pr https://github.com/octocat/Hello-World/pull/6
python claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3297
```
