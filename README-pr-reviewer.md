# PR Reviewer Agent

`claude-review` reviews a GitHub pull request and prints a structured Markdown
comment with a summary, risks, suggestions, and confidence score.

## Setup

No dependencies are required beyond Python 3.11+.

## Usage

```bash
python bin/claude-review --pr https://github.com/owner/repo/pull/123
```

The output can be pasted into the pull request conversation. If using Claude
Code, load `agents/pr-reviewer.md` as the agent instruction and let it run the
same command before posting or returning the comment.

## Sample Outputs

Two real-PR sample outputs are included:

- `examples/review-urllib3-5061.md`
- `examples/review-claude-builders-2105.md`
