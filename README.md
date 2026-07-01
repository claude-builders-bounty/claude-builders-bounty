# claude-review

A CLI tool that reviews GitHub PR diffs and produces structured Markdown output.

**Bounty**: [$150 — Issue #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## Usage

```bash
# CLI mode
./claude-review --pr https://github.com/owner/repo/pull/123

# With a GitHub token (required for private repos / higher rate limits)
./claude-review --pr https://github.com/owner/repo/pull/123 --token ghp_xxx

# Or set as env var
export GITHUB_TOKEN=ghp_xxx
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Output Format

The tool outputs a structured Markdown review with:
- **Summary**: files changed, lines added
- **⚠️ Risks**: security concerns (hardcoded secrets, dangerous functions, unsafe patterns)
- **💡 Improvements**: code quality suggestions
- **Confidence Score**: Low / Medium / High

## GitHub Action

A GitHub Action workflow is included (`.github/workflows/claude-review.yml`).
It runs on `/review` comments and posts the review output as a PR comment.

## Requirements

- Python 3.10+
- No external dependencies (uses only stdlib)

## Sample Output

See `examples/` for sample reviews on real PRs.
