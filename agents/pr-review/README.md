# claude-review — PR Review Agent

Claude Code agent that analyzes PR diffs and returns structured Markdown reviews.

## Setup

```bash
chmod +x claude-review.sh
```

## Usage

```bash
# Review a PR
./claude-review.sh --pr https://github.com/owner/repo/pull/123

# Review and post as comment
./claude-review.sh --pr https://github.com/owner/repo/pull/123 --post
```

## Example Output

See `sample-reviews/` for real PR review examples.

## Requirements

- `gh` CLI (authenticated)
- `bash` 4+
