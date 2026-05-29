# Claude PR Reviewer Agent

`claude-review` reviews a GitHub pull request and returns a structured Markdown comment with a summary, risks, improvement suggestions, and a confidence score.

## Setup

1. Copy `claude-review.py` into a directory on your `PATH` as `claude-review`.
2. Set `GITHUB_TOKEN` for private repos or higher rate limits, and set `ANTHROPIC_API_KEY` to use Claude.
3. Run `claude-review --pr https://github.com/owner/repo/pull/123`.

If `ANTHROPIC_API_KEY` is not set, the CLI uses a deterministic local reviewer. This keeps tests and examples reproducible without exposing secrets.

## Usage

```bash
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2266
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
claude-review --pr https://github.com/owner/repo/pull/123 --heuristic
```

The output always contains:

- `## Summary`
- `## Identified Risks`
- `## Improvement Suggestions`
- `## Confidence`

## GitHub Action

Copy `github-action.yml` to `.github/workflows/claude-review.yml` in a repository and add `ANTHROPIC_API_KEY` as a repository secret. The workflow runs on pull requests, generates `review.md`, and uploads it as an artifact. Uncomment the final `gh pr comment` step if you want automatic PR comments.

## Validation

```bash
python -m unittest discover -s agents/pr-reviewer/tests -p test_*.py
python agents/pr-reviewer/claude-review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2266 --heuristic
```

Sample outputs from two real PRs are included in `samples/`.
