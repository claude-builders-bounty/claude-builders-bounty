# PR Reviewer Agent

This agent reviews a GitHub pull request diff and returns a structured Markdown comment with a summary, risks, suggestions, and confidence score.

## Setup

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

To save the review:

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## Output Format

- `Summary`: 2 or 3 sentences describing scope and touched areas.
- `Identified Risks`: concrete risks detected from the diff.
- `Improvement Suggestions`: practical next steps for reviewers or authors.
- `Confidence`: `Low`, `Medium`, or `High`.

## Notes

The CLI can also review a local diff with `--diff-file path/to/change.diff`, which makes it useful in CI or local pre-review workflows.
