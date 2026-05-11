# Claude PR Review Agent

`claude-review` is a small Claude Code-friendly CLI that reviews a GitHub pull request diff and emits a structured Markdown comment.

## Setup

1. Copy or keep `pr-review-agent/claude_review.py` in your repo.
2. Run it with Python 3.10+.
3. Optional: set `GITHUB_TOKEN` if you want authenticated fetching or comment posting.

## Usage

Generate a Markdown review:

```bash
python3 pr-review-agent/claude_review.py --pr https://github.com/owner/repo/pull/123
```

Save the review:

```bash
python3 pr-review-agent/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post the review as a PR comment:

```bash
GITHUB_TOKEN=ghp_xxx python3 pr-review-agent/claude_review.py --pr https://github.com/owner/repo/pull/123 --post-comment
```

Use a locally saved diff:

```bash
python3 pr-review-agent/claude_review.py --pr https://github.com/owner/repo/pull/123 --diff-file pr.diff
```

## Output Format

The generated comment always includes:

- Summary of changes in 2 short paragraphs
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

## Notes

The default reviewer is deterministic and dependency-free so it works in Claude Code, CI, and local shells. It focuses on diff shape, changed file types, and common risk patterns. Teams can wrap this script in a Claude Code sub-agent or GitHub Action and pass the generated Markdown to a stronger model for deeper semantic review.
