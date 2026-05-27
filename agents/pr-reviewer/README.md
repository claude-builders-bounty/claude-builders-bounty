# Claude PR Review Agent

`claude-review` reads a GitHub pull request diff and returns a structured Markdown review comment.

## Setup

```bash
export GITHUB_TOKEN=ghp_optional_token_for_private_repos_or_higher_rate_limits
```

## Usage

```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

For a local executable:

```bash
chmod +x agents/pr-reviewer/claude-review
PATH="$PWD/agents/pr-reviewer:$PATH" claude-review --pr https://github.com/owner/repo/pull/123
```

## Output Format

The generated Markdown contains:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: `Low`, `Medium`, or `High`

The analysis is intentionally conservative. It uses the PR diff, changed file paths, test-file detection, changed-line count, and risky pattern checks. It does not approve code by itself; it gives reviewers a structured first pass.

## Sample Outputs

See:

- [`sample-outputs/python-cpython-120000.md`](sample-outputs/python-cpython-120000.md)
- [`sample-outputs/psf-requests-6700.md`](sample-outputs/psf-requests-6700.md)
