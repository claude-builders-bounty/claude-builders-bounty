# Claude PR Reviewer

Structured PR review agent for Claude Code bounty #4.

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Offline/local diff mode:

```bash
python agents/pr-reviewer/claude_review.py --diff-file samples/pr-reviewer/sample_pr_with_tests.diff
cat change.diff | python agents/pr-reviewer/claude_review.py
```

The agent prints a Markdown review comment with:

- Summary of changes (2–3 sentences)
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## Notes

- `--pr` fetches the public GitHub PR diff from GitHub's `.diff` endpoint.
- No GitHub token is required for public PRs.
- For private repositories, export/download the PR diff and use `--diff-file` or stdin.


## CLI entrypoint

Run `./claude-review --pr https://github.com/owner/repo/pull/123` from the repository root. You can also place `claude-review` on your PATH to use it as `claude-review --pr ...`.
