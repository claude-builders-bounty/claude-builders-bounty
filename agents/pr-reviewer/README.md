# Claude PR Review Agent

`claude-review` reads a GitHub pull request diff and returns a structured
Markdown review comment with a summary, risk list, improvement suggestions, and
confidence score.

## Setup

1. Add `agents/pr-reviewer/bin` to your `PATH`.
2. Run `claude-review --pr https://github.com/owner/repo/pull/123`.
3. Optionally write the review directly to a file with `--output review.md`.
4. Optionally post the generated review directly with `--post-comment`.
5. Add any project-specific test notes before relying on the generated review.

For private repositories or higher GitHub API limits, set `GITHUB_TOKEN` before
running the CLI. The token is used only as an Authorization header when fetching
the PR diff from GitHub's REST API. `--post-comment` uses `GITHUB_TOKEN` or
`GH_TOKEN` to call the pull request's issue-comments endpoint.

## Claude Code Sub-Agent

The companion sub-agent definition lives at `.claude/agents/pr-reviewer.md`.
Use it when you want Claude Code to run the CLI, inspect the output, and add
repository-specific context before posting a review.

## Local Diff Mode

For offline testing or CI:

```bash
claude-review --diff-file path/to/change.diff
# Equivalent shorter form:
claude-review --diff path/to/change.diff
claude-review --diff path/to/change.diff --output review.md
```

## Large Diff Handling

Reviews analyze the first 120,000 diff characters. If a PR exceeds that cap,
the output includes a truncation warning and uses a Low confidence score so the
omitted portion is not silently treated as reviewed.

## Risk Detection

The reviewer flags common diff hazards such as shell execution, destructive
commands, credential handling, DOM injection, plain HTTP URLs, silent exception
handlers, debug output, permissive CORS, unscoped database mutation, and risky
GitHub Actions changes such as `pull_request_target` or broad write
permissions.

## Optional GitHub Action Commenter

`.github/workflows/claude-review-comment.yml` can post the generated Markdown
directly to a PR in the current repository. Run the workflow manually, pass the
PR URL, and the workflow will:

1. Generate `review.md` with `agents/pr-reviewer/claude_review.py --pr --output`.
2. Refuse URLs outside the current repository.
3. Post the structured review with the CLI's `--post-comment` mode.

## Sample PR Outputs

Two real GitHub PR review outputs are included for bounty verification:

- `agents/pr-reviewer/samples/claude-builders-pr-2710.md`
- `agents/pr-reviewer/samples/claude-builders-pr-2738.md`

## Validation

```bash
python3 -m unittest tests/test_claude_review.py -v
python3 -m py_compile agents/pr-reviewer/claude_review.py tests/test_claude_review.py
git diff --check
```
