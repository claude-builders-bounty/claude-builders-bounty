# Claude PR Review Agent

Generate a structured Markdown review for a GitHub pull request.

## Usage

```bash
python3 scripts/claude_review.py --pr https://github.com/owner/repo/pull/123
```

Optional for private repos or higher rate limits:

```bash
export GITHUB_TOKEN=ghp_xxx
python3 scripts/claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Output format

The agent prints:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## Notes

This is intentionally dependency-free. It uses GitHub's REST API and diff media type, then applies static heuristics for risky paths, secrets, auth changes, SQL/destructive operations, diff size, and missing tests.

It is a reviewer assistant, not an auto-approval bot. Pair the output with repository-specific tests before merge.
